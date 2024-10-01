import { Injectable } from "@angular/core";
import { ChatMessageService } from "../chat-message/chat-message.service";
import { AudioPlayerService } from "../audio-player/audio-player.service";
import { EndpointService } from "../endpoint/endpoint.service";
import { GeneralProfile, Profile } from "../../types/profile.type";
import { Message, MessageRole } from "../../types/message.type";
import { createId } from "@paralleldrive/cuid2";
import { ProfileService } from "../profile/profile.service";
import { BehaviorSubject, takeWhile, takeUntil } from "rxjs";
import { convertBase64ToBlob } from "../../utils/base-64-to-blob";
import { VadService } from "../vad/vad.service";
import { PreferenceService } from "../preference/preference.service";
import { AudioService } from "../audio/audio.service";
import { MicState } from "../../types/mic-state.type";
import { VoiceActivity } from "../../types/voice-activity.type";
import { ActivatedRoute } from "@angular/router";
import { ChatMode } from "../../types/chat-mode.type";
import { v2AudioRecorder } from "../../utils/v2/audio-recorder-v2";
import { Feedback } from "../../types/feedback.type";
import { Language } from "../../types/language.type";
import { Subject } from "rxjs";
import { APP_CONSTANTS } from "../../constants";

@Injectable({
  providedIn: "root"
})
export class ConvoBrokerService {
  private recorder!: v2AudioRecorder;
  private activeProfile: BehaviorSubject<Profile | undefined> = new BehaviorSubject<Profile | undefined>(undefined);

  $language: BehaviorSubject<string> = new BehaviorSubject<string>(Language.Spoken);

  $micState: BehaviorSubject<MicState> = new BehaviorSubject<MicState>(MicState.PENDING);
  $isWaitingForVoiceApi: BehaviorSubject<boolean> = new BehaviorSubject<boolean>(false);
  $sendTimeout: BehaviorSubject<boolean> = new BehaviorSubject<boolean>(false);

  constructor(
    private chatMessageService: ChatMessageService,
    private audioPlayer: AudioPlayerService,
    private endpointService: EndpointService,
    private preferenceService: PreferenceService,
    private profileService: ProfileService,
    private vadService: VadService
  ) {
    this.initVoiceChat().catch(console.error);
    this.profileService.$currentProfileInUrl.subscribe(p => {
      this.activeProfile = this.profileService.getProfile(p);
    });
    this.preferenceService.$language.subscribe(l => {
      this.$language.next(l);
    });
  }

  /**
   * Method to initialise voice monitoring for voice activity detection
   * @private
   */
  private async initVoiceChat() {
    // this.recorder = new AudioRecorder(await this.audioService.getMicInput());
    this.recorder = new v2AudioRecorder(this.chatMessageService, this.profileService);

    // Subscriber to "open" the mic for user once API call has been completed
    this.$isWaitingForVoiceApi.subscribe(v => {
      if (!v) {
        this.$micState.next(MicState.PENDING);
      }
    });

    // Monitor VAD activity
    this.vadService.start().subscribe({
      next: s => {
        // DO NOT DO ANYTHING if chat mode is not voice
        if (this.preferenceService.$chatMode.value !== ChatMode.Voice) {
          return;
        }

        switch (s) {
          case VoiceActivity.Start: {
            if (
              this.preferenceService.$voiceDetectStart.value &&
              this.$micState.value === MicState.PENDING &&
              !this.$isWaitingForVoiceApi.value &&
              ((this.audioPlayer.$playing.value && this.preferenceService.$voiceDetectInterrupt.value) || !this.audioPlayer.$playing.value)
            ) {
              this.handleStartRecording();
            }
            break;
          }

          case VoiceActivity.End: {
            if (this.preferenceService.$voiceDetectEnd.value && this.$micState.value === MicState.ACTIVE) {
              this.handleStopRecording();
            }
            break;
          }
        }
      }
    });
  }

  openWebSocket() {
    this.recorder.setupWebSocket();
  }

  closeWebSocket() {
    this.recorder.closeWebSocket();
  }

  /**
   * Method to trigger the start of audio recording
   * @private
   */
  handleStartRecording() {
    this.audioPlayer.stopAndClear();
    this.audioPlayer.playStartVoiceAudio();
    this.$micState.next(MicState.ACTIVE);
    // this.recorder.start();
    this.recorder.startAudioCapture();
  }

  /**
   * Method to stop the recording, and handle post-processing of recorded audio
   * @private
   */
  private handleStopRecording() {
    this.audioPlayer.playStopVoiceAudio();
    this.$micState.next(MicState.DISABLED);
    this.recorder.stopAudioCapture().then(r => {
      this.sendVoice(r, this.activeProfile.value || GeneralProfile).catch(console.error);
    });
  }

  /**
   * Method to handle stopping audio playback
   * @private
   */
  private handleStopPlaying() {
    this.audioPlayer.stopAndClear();
    this.$micState.next(MicState.PENDING);
  }

  /**
   * Method to convert string to blob and play the blob.
   * @param val {string} Base 64 encoding of an audio blob
   * @private
   */
  async playAudioBase64(val: string): Promise<void> {
    const audioBlob = convertBase64ToBlob(val, "audio/mp3");
    this.audioPlayer.play(audioBlob);
  }
  /**
   * Method to send the transcribed text as a request to the backend.
   * Handled by `EndpointService`
   * @param message {string}
   * @param profile {Profile}
   * @private
   */

  private async sendVoice(message: string, profile: Profile) {
    this.$isWaitingForVoiceApi.next(true);

    const requestTime: number = new Date().getTime();
    const userMessageId = createId();
    const assistantMessageId: string = createId();

    const history: Message[] = await this.chatMessageService.staticLoad(profile.id);

    let audio_base64: string[] = [];

    // Subject to cancel the observable when timeout occurs
    const cancel$ = new Subject<void>();

    const res = await this.endpointService.sendVoice(
      message,
      this.activeProfile.value || GeneralProfile,
      history.slice(-8),
      this.$language.value || Language.Spoken
    );

    const timeoutPromise = new Promise<void>(resolve => {
      setTimeout(() => {
        this.$sendTimeout.next(true);
        // Emit a value to cancel the observable
        cancel$.next();
        resolve();
      }, APP_CONSTANTS.VOICE_TIMEOUT);
    });

    const responsePromise = new Promise<void>(resolve => {
      res
        .pipe(
          takeWhile(d => d?.status !== "DONE", true),
          takeUntil(cancel$) // Cancel the observable if timeout occurs
        )
        .subscribe({
          next: async d => {
            if (!d) {
              return;
            }

            // upsert assistant message
            await this.chatMessageService.upsert({
              id: assistantMessageId,
              profile_id: profile.id,
              role: MessageRole.Assistant,
              message: d.assistant_response,
              timestamp: new Date().getTime(),
              sources: d.sources
            });

            const nonNullAudio = d.assistant_response_audio.map(v => v);
            if (nonNullAudio.length > audio_base64.length) {
              const newAudioStr = nonNullAudio.filter(a => !audio_base64.includes(a));
              audio_base64 = nonNullAudio;

              // set mic state to pending so the loading throbber is removed.
              this.$micState.next(MicState.PENDING);

              newAudioStr.forEach(a => {
                this.playAudioBase64(a);
              });
            }
          },
          complete: () => {
            resolve(); // Complete the response handling
          },
          error: () => {
            resolve(); // Also resolve in case of an error
          }
        });
    });

    await Promise.race([responsePromise, timeoutPromise]);

    // Complete the cancel subject to clean up resources
    cancel$.complete();

    // Handle timeout or completion
    this.$isWaitingForVoiceApi.next(false);
  }

  async sendFeedback(feedback: Feedback) {
    const profile_id = this.profileService.$currentProfileInUrl.value;
    const history: Message[] = (await this.chatMessageService.staticLoad(profile_id)).slice(-8);

    const updated_feedback: Feedback = {
      label: feedback.label,
      category: feedback.category,
      remarks: feedback.remarks,
      chat_history: history,
      profile_id: profile_id,
      datetime: feedback.datetime
    };
    console.log("Updated Feedback: ", updated_feedback);

    const profile = this.profileService.getProfile(this.profileService.$currentProfileInUrl.value).value!;

    await this.endpointService.sendFeedback(updated_feedback, profile);
  }

  /**
   * Callback method to be called from anywhere to directly interact with audio recording/voice interaction.
   */
  handleMicButtonClick() {
    switch (this.$micState.value) {
      case MicState.ACTIVE:
        this.handleStopRecording();
        break;
      case MicState.PENDING:
        if (this.audioPlayer.$playing.value) {
          this.handleStopPlaying();
        } else {
          this.handleStartRecording();
        }
        break;
      default:
        console.warn("Unhandled mic state:", this.$micState.value);
        break;
    }
  }

  /**
   * Method to persist chat message, and send the chat message to the backend for LLM generation.
   * @param message {string}
   * @param profile {Profile}
   */
  async sendChat(message: string, profile: Profile) {
    const newMessage: Message = {
      id: createId(),
      message: message,
      profile_id: profile.id,
      role: MessageRole.User,
      timestamp: new Date().getTime(),
      sources: []
    };
    const responseMessageId = createId();

    const history: Message[] = (await this.chatMessageService.staticLoad(profile.id)).slice(-8);

    await this.chatMessageService.insert(newMessage);

    const res = await this.endpointService.sendChat(newMessage, profile, history, this.$language.value || Language.Spoken);
    res.pipe(takeWhile(d => d?.status !== "DONE", true)).subscribe({
      next: async d => {
        if (!d || !d.response) {
          return;
        }
        await this.chatMessageService.upsert({
          id: responseMessageId,
          profile_id: profile.id,
          message: d.response,
          timestamp: new Date().getTime(),
          role: MessageRole.Assistant,
          sources: d.sources
        });
      },
      error: console.error
    });
  }
}
