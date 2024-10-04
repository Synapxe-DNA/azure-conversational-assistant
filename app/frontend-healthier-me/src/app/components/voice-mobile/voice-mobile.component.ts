import { AfterViewInit, Component, Input, OnInit } from "@angular/core";
import { PreferenceService } from "../../services/preference/preference.service";
import { WaveformComponent } from "../waveform/waveform.component";
import { MicrophoneButtonComponent } from "../microphone-button/microphone-button.component";
import { MicState } from "../../types/mic-state.type";
import { SecondaryButtonComponent } from "../secondary-button/secondary-button.component";
import { LucideAngularModule } from "lucide-angular";
import { Button } from "primeng/button";
import { OverlayPanelModule } from "primeng/overlaypanel";
import { InputSwitchChangeEvent, InputSwitchModule } from "primeng/inputswitch";
import { ChatMode } from "../../types/chat-mode.type";
import { FormsModule } from "@angular/forms";
import { AudioRecorder } from "../../utils/audio-recorder";
import { AudioService } from "../../services/audio/audio.service";
import { VoiceActivity } from "../../types/voice-activity.type";
import { BehaviorSubject, takeWhile } from "rxjs";
import { ActivatedRoute } from "@angular/router";
import { GeneralProfile, Profile } from "../../types/profile.type";
import { ProfileService } from "../../services/profile/profile.service";
import { ConvoBrokerService } from "../../services/convo-broker/convo-broker.service";
import { TextComponent } from "../text/text.component";
import { VoiceSourcesComponent } from "./voice-sources/voice-sources.component";
import { VoiceMessageComponent } from "./voice-message/voice-message.component";
import { VoiceAnnotationComponent } from "./voice-annotation/voice-annotation.component";
import { VoiceMicrophoneComponent } from "./voice-microphone/voice-microphone.component";
import { Message, MessageRole, MessageSource } from "../../types/message.type";
import { ChatMessageService } from "../../services/chat-message/chat-message.service";
import { v2AudioRecorder } from "../../utils/v2/audio-recorder-v2";
import { CommonModule } from "@angular/common";
import { DialogModule } from "primeng/dialog";

@Component({
  selector: "app-voice-mobile",
  standalone: true,
  imports: [
    WaveformComponent,
    MicrophoneButtonComponent,
    SecondaryButtonComponent,
    LucideAngularModule,
    Button,
    OverlayPanelModule,
    InputSwitchModule,
    FormsModule,
    TextComponent,
    CommonModule,
    DialogModule,
    VoiceSourcesComponent,
    VoiceMessageComponent,
    VoiceAnnotationComponent,
    VoiceMicrophoneComponent
  ],
  templateUrl: "./voice-mobile.component.html",
  styleUrl: "./voice-mobile.component.css"
})
export class VoiceMobileComponent {
  private isUserTurn: BehaviorSubject<boolean> = new BehaviorSubject<boolean>(true);
  private recorder: v2AudioRecorder | undefined;
  profile: BehaviorSubject<Profile | undefined> = new BehaviorSubject<Profile | undefined>(undefined);

  micState: MicState = MicState.PENDING;
  message?: Message;
  chatMode?: ChatMode;
  isLoading: boolean = false;
  sendTimedOut: boolean = false;
  showTimeoutModal = false;

  voiceInterrupt: boolean = false;
  voiceDetectStart: boolean = false;
  voiceDetectEnd: boolean = false;
  showLiveTranscription: boolean = false;

  constructor(
    private preference: PreferenceService,
    private route: ActivatedRoute,
    private profileService: ProfileService,
    private convoBroker: ConvoBrokerService,
    private chatMessageService: ChatMessageService,
    private preferences: PreferenceService
  ) {
    this.message = {
      role: MessageRole.Assistant,
      sources: [],
      timestamp: 0,
      id: "",
      profile_id: "",
      message: ""
    };
    this.preferences.$chatMode.subscribe(m => {
      this.chatMode = m;
    });
  }

  ngOnInit() {
    this.profileService.setProfileInUrl(this.route.snapshot.paramMap.get("profileId")!);

    this.preference.$voiceDetectInterrupt.subscribe(v => {
      this.voiceInterrupt = v;
    });
    this.preference.$voiceDetectStart.subscribe(v => (this.voiceDetectStart = v));
    this.preference.$voiceDetectEnd.subscribe(v => (this.voiceDetectEnd = v));
    this.preference.$showLiveTranscription.subscribe(v => (this.showLiveTranscription = v));
    this.convoBroker.$micState.subscribe(v => {
      this.micState = v;
      this.isLoading = v === MicState.DISABLED;
      console.log(this.micState);
      console.log(this.isLoading);
    });
    this.convoBroker.$sendTimeout.subscribe(timeoutOccurred => {
      this.sendTimedOut = timeoutOccurred;

      if (this.sendTimedOut) {
        // Handle the timeout state in the UI (e.g., display an error message)
        this.showTimeoutPopup();
      }
    });
  }

  ngAfterViewInit() {
    this.profile = this.profileService.getProfile(this.route.snapshot.paramMap.get("profileId") as string);

    this.profile.subscribe(p => {
      if (!p) {
        return;
      }
      this.chatMessageService.load(p.id).then(m => {
        m.subscribe(messages => {
          this.message = messages.sort((b, a) => a.timestamp - b.timestamp)[0];
        });
      });
    });
    this.initVoiceChat().catch(console.error);
  }

  private async initVoiceChat() {
    this.recorder = new v2AudioRecorder(this.chatMessageService, this.profileService);
  }

  handleMicButtonClick() {
    this.convoBroker.handleMicButtonClick();
  }

  prefChatModeToText(): void {
    this.preference.setChatMode(ChatMode.Text);
  }

  prefVoiceInterrupt(e: InputSwitchChangeEvent) {
    this.preference.setVoiceDetectInterrupt(e.checked);
  }

  prefVoiceStart(e: InputSwitchChangeEvent) {
    this.preference.setVoiceDetectStart(e.checked);
  }

  prefVoiceEnd(e: InputSwitchChangeEvent) {
    this.preference.setVoiceDetectEnd(e.checked);
  }

  toggleChatMode() {
    switch (this.chatMode) {
      case ChatMode.Voice:
        this.preferences.setChatMode(ChatMode.Text);
        break;
      case ChatMode.Text:
        this.preferences.setChatMode(ChatMode.Voice);
        break;
    }
  }

  showTimeoutPopup() {
    this.showTimeoutModal = true;
  }

  closeTimeoutPopup() {
    this.showTimeoutModal = false;
  }
}
