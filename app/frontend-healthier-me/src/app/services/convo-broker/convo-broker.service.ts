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

@Injectable({
  providedIn: "root",
})
export class ConvoBrokerService {
  private recorder!: AudioRecorder;
  private activeProfile: Profile | undefined;

  $micState: BehaviorSubject<MicState> = new BehaviorSubject<MicState>(
    MicState.PENDING,
  );
  $isWaitingForVoiceApi: BehaviorSubject<boolean> =
    new BehaviorSubject<boolean>(false);

  constructor(
    private chatMessageService: ChatMessageService,
    private audioPlayer: AudioPlayerService,
    private endpointService: EndpointService,
    private preferenceService: PreferenceService,
    private profileService: ProfileService,
    private vadService: VadService,
    private audioService: AudioService,
    private route: ActivatedRoute,
  ) {
    this.initVoiceChat().catch(console.error);
    this.profileService
      .getProfile(this.route.snapshot.paramMap.get("profileId") as string)
      .subscribe((d) => (this.activeProfile = d || GeneralProfile));
  }

  private async playAudioBase64(val: string): Promise<void> {
    const audioBlob = convertBase64ToBlob(val, "audio/*");
    this.audioPlayer.play(audioBlob);
  }

  private async initVoiceChat() {
    this.recorder = new AudioRecorder(await this.audioService.getMicInput());
    this.$isWaitingForVoiceApi.subscribe((v) => {
      if (!v) {
        this.$micState.next(MicState.PENDING);
      }
    });

    this.vadService.start().subscribe({
      next: (s) => {
        switch (s) {
          case VoiceActivity.Start: {
            if (
              this.preferenceService.$voiceDetectStart.value &&
              this.$micState.value === MicState.PENDING &&
              !this.$isWaitingForVoiceApi.value &&
              ((this.audioPlayer.$playing.value &&
                this.preferenceService.$voiceDetectInterrupt.value) ||
                !this.audioPlayer.$playing.value)
            ) {
              this.handleStartRecording();
            }
            break;
          }

          case VoiceActivity.End: {
            if (
              this.preferenceService.$voiceDetectEnd.value &&
              this.$micState.value === MicState.ACTIVE
            ) {
              this.handleStopRecording();
            }
            break;
          }
        }
      },
    });
  }

  private handleStartRecording() {
    this.$micState.next(MicState.ACTIVE);
    this.audioPlayer.stop();
    this.recorder.start();
  }

  private handleStopRecording() {
    this.$micState.next(MicState.DISABLED);
    this.recorder.stop().then((r) => {
      this.sendVoice(r.data, this.activeProfile || GeneralProfile).catch(
        console.error,
      );
    });
  }

  async sendVoice(audio: Blob, profile: Profile) {
    this.$isWaitingForVoiceApi.next(true);

    const requestTime: number = new Date().getTime();
    const userMessageId = createId();
    const assistantMessageId: string = createId();

    const history: Message[] = await this.chatMessageService.staticLoad(
      profile.id,
    );

    let audio_base64: string = "";

    const res = await this.endpointService.sendVoice(
      audio,
      profile || GeneralProfile,
      history.slice(-8),
    );
    res.pipe(takeWhile((d) => d?.status !== "DONE", true)).subscribe({
      next: async (d) => {
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
        });

        // upsert assistant message
        await this.chatMessageService.upsert({
          id: assistantMessageId,
          profile_id: profile.id,
          role: MessageRole.Assistant,
          message: d.assistant_response,
          timestamp: new Date().getTime(),
        });

        audio_base64 = d.assistant_response_audio;
      },
      complete: () => {
        this.$isWaitingForVoiceApi.next(false);
        this.playAudioBase64(audio_base64);
      },
    });
  }

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

  async sendChat(message: string, profile: Profile) {
    const newMessage: Message = {
      id: createId(),
      message: message,
      profile_id: profile.id,
      role: MessageRole.User,
      timestamp: new Date().getTime(),
    };

    const history: Message[] = await this.chatMessageService.staticLoad(
      profile.id,
    );
    (
      await this.endpointService.sendChat(newMessage, profile, history)
    ).subscribe(console.log);
  }
}
