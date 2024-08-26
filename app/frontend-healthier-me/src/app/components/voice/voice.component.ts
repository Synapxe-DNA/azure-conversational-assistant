import { AfterViewInit, Component, OnInit } from "@angular/core";
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
import { VadService } from "../../services/vad/vad.service";
import { AudioService } from "../../services/audio/audio.service";
import { VoiceActivity } from "../../types/voice-activity.type";
import { BehaviorSubject, takeWhile } from "rxjs";
import { ActivatedRoute } from "@angular/router";
import { GeneralProfile, Profile } from "../../types/profile.type";
import { ProfileService } from "../../services/profile/profile.service";
import { ConvoBrokerService } from "../../services/convo-broker/convo-broker.service";
import { TextComponent } from "../text/text.component";

@Component({
    selector: "app-voice",
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
        TextComponent
    ],
    templateUrl: "./voice.component.html",
    styleUrl: "./voice.component.css"
})
export class VoiceComponent implements OnInit, AfterViewInit {
    private isUserTurn: BehaviorSubject<boolean> = new BehaviorSubject<boolean>(true);
    private recorder: AudioRecorder | undefined;
    private profile: Profile | undefined;

    micState: MicState = MicState.PENDING;

    voiceInterrupt: boolean = false;
    voiceDetectStart: boolean = false;
    voiceDetectEnd: boolean = false;
    showLiveTranscription: boolean = false;

    constructor(
        private preference: PreferenceService,
        private audio: AudioService,
        private route: ActivatedRoute,
        private profileService: ProfileService,
        private convoBroker: ConvoBrokerService
    ) {}

    ngOnInit() {
        this.profileService.setProfileInUrl(this.route.snapshot.paramMap.get("profileId")!);

        this.preference.$voiceDetectInterrupt.subscribe(v => {
            this.voiceInterrupt = v;
        });
        this.preference.$voiceDetectStart.subscribe(v => (this.voiceDetectStart = v));
        this.preference.$voiceDetectEnd.subscribe(v => (this.voiceDetectEnd = v));
        this.preference.$showLiveTranscription.subscribe(v => (this.showLiveTranscription = v));
        this.convoBroker.$micState.subscribe(v => (this.micState = v));
    }

    ngAfterViewInit() {
        this.profileService.getProfile(this.route.snapshot.paramMap.get("profileId") as string).subscribe(d => (this.profile = d || GeneralProfile));
        this.initVoiceChat().catch(console.error);
    }

    private async initVoiceChat() {
        this.recorder = new AudioRecorder(await this.audio.getMicInput());
    }

    handleMicButtonClick() {
        this.convoBroker.handleMicButtonClick();
    }

    prefChatModeToText(): void {
        this.preference.setChatMode(ChatMode.Text);
    }

    prefShowLiveTranscription(e: InputSwitchChangeEvent) {
        this.preference.setShowLiveTranscription(e.checked);
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
}
