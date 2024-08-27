import { Injectable } from "@angular/core";
import { ChatMessageService } from "../chat-message/chat-message.service";
import { AudioPlayerService } from "../audio-player/audio-player.service";
import { EndpointService } from "../endpoint/endpoint.service";
import { GeneralProfile, Profile } from "../../types/profile.type";
import { Message, MessageRole } from "../../types/message.type";
import { createId } from "@paralleldrive/cuid2";
import { ProfileService } from "../profile/profile.service";
import { BehaviorSubject, takeWhile } from "rxjs";
import { convertBase64ToBlob } from "../../utils/base-64-to-blob";
import { VadService } from "../vad/vad.service";
import { PreferenceService } from "../preference/preference.service";
import { AudioService } from "../audio/audio.service";
import { MicState } from "../../types/mic-state.type";
import { AudioRecorder } from "../../utils/audio-recorder";
import { VoiceActivity } from "../../types/voice-activity.type";
import { ActivatedRoute } from "@angular/router";
import { ChatMode } from "../../types/chat-mode.type";
import { v2AudioRecorder } from "../../utils/v2/audio-recorder-v2";
import { Language } from "../../types/language.type";

@Injectable({
  providedIn: "root"
})
export class ConvoBrokerService {
  private recorder!: AudioRecorder;
  private recorder2!: v2AudioRecorder;
  private activeProfile: BehaviorSubject<Profile | undefined> = new BehaviorSubject<Profile | undefined>(undefined);

  $language: BehaviorSubject<string> = new BehaviorSubject<string>(Language.Spoken);

  $micState: BehaviorSubject<MicState> = new BehaviorSubject<MicState>(MicState.PENDING);
  $isWaitingForVoiceApi: BehaviorSubject<boolean> = new BehaviorSubject<boolean>(false);

  constructor(
    private chatMessageService: ChatMessageService,
    private audioPlayer: AudioPlayerService,
    private endpointService: EndpointService,
    private preferenceService: PreferenceService,
    private profileService: ProfileService,
    private vadService: VadService,
    private audioService: AudioService,
    private route: ActivatedRoute
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
    this.recorder2 = new v2AudioRecorder(this.chatMessageService, this.profileService);

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

  /**
   * Method to trigger the start of audio recording
   * @private
   */
  private handleStartRecording() {
    this.$micState.next(MicState.ACTIVE);
    this.audioPlayer.stopAndClear();
    // this.recorder.start();
    this.recorder2.setupWebSocket();
  }

  /**
   * Method to stop the recording, and handle post-processing of recorded audio
   * @private
   */
  private handleStopRecording() {
    this.$micState.next(MicState.DISABLED);

    // this.recorder.stop().then((r) => {
    //   this.sendVoice(r.data, this.activeProfile.value || GeneralProfile).catch(
    //     console.error,
    //   );
    // });

    this.recorder2.stopAudioCapture().then(r => {
      this.recorder2.socket?.close();
      this.sendVoice2(r, this.activeProfile.value || GeneralProfile).catch(console.error);
    });
  }

  /**
   * Method to convert string to blob and play the blob.
   * @param val {string} Base 64 encoding of an audio blob
   * @private
   */
  private async playAudioBase64(val: string): Promise<void> {
    const audioBlob = convertBase64ToBlob(val, "audio/*");
    this.audioPlayer.play(audioBlob);
  }

  /**
   * Method to send the voice blob as a request to the backend.
   * Handled by `EndpointService`
   * @param audio {Blob}
   * @param profile {Profile}
   * @private
   */
  private async sendVoice(audio: Blob, profile: Profile) {
    this.$isWaitingForVoiceApi.next(true);

    const requestTime: number = new Date().getTime();
    const userMessageId = createId();
    const assistantMessageId: string = createId();

    const history: Message[] = await this.chatMessageService.staticLoad(profile.id);

    let audio_base64: string[] = [];

    const res = await this.endpointService.sendVoice(audio, this.activeProfile.value || GeneralProfile, history.slice(-8));
    res.pipe(takeWhile(d => d?.status !== "DONE", true)).subscribe({
      next: async d => {
        if (!d) {
          return;
        }

        // upsert user message
        await this.chatMessageService.upsert({
          id: userMessageId,
          profile_id: profile.id,
          role: MessageRole.User,
          message: d.user_transcript,
          timestamp: requestTime,
          sources: []
        });

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
          newAudioStr.forEach(a => {
            this.playAudioBase64(a);
          });
        }
      },
      complete: () => {
        this.$isWaitingForVoiceApi.next(false);
      }
    });
  }

  /**
   * Method to send the transcribed text as a request to the backend.
   * Handled by `EndpointService`
   * @param message {string}
   * @param profile {Profile}
   * @private
   */
  private async sendVoice2(message: string, profile: Profile) {
    this.$isWaitingForVoiceApi.next(true);

    const requestTime: number = new Date().getTime();
    const userMessageId = createId();
    const assistantMessageId: string = createId();

    const history: Message[] = await this.chatMessageService.staticLoad(profile.id);

    let audio_base64: string[] = [];

    const res = await this.endpointService.sendVoice2(
      message,
      this.activeProfile.value || GeneralProfile,
      history.slice(-8),
      this.$language.value || Language.Spoken
    );
    res.pipe(takeWhile(d => d?.status !== "DONE", true)).subscribe({
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
          newAudioStr.forEach(a => {
            this.playAudioBase64(a);
          });
        }
      },
      complete: () => {
        this.$isWaitingForVoiceApi.next(false);
      }
    });
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
        this.handleStartRecording();
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

        // Plan to create follow_up indexDB here
      },
      error: console.error
    });
  }
}
