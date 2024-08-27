import { AfterViewInit, Component, ElementRef, EventEmitter, Input, OnChanges, Output, SimpleChanges, ViewChild } from "@angular/core";
import { CommonModule } from "@angular/common";
import { LucideAngularModule } from "lucide-angular";
import { MicState } from "../../../types/mic-state.type";
import { AudioService } from "../../../services/audio/audio.service";
import { AudioAnalyser } from "../../../utils/audio-analyser";
import { WaveformComponent } from "../../waveform/waveform.component";
import { BehaviorSubject } from "rxjs/internal/BehaviorSubject";
import { AudioPlayerService } from "../../../services/audio-player/audio-player.service";

@Component({
  selector: "app-voice-microphone",
  standalone: true,
  imports: [CommonModule, LucideAngularModule, WaveformComponent],
  templateUrl: "./voice-microphone.component.html",
  styleUrl: "./voice-microphone.component.css"
})
export class VoiceMicrophoneComponent {
  @Input() state!: MicState;

  @ViewChild("btn") btn!: ElementRef<HTMLButtonElement>;

  @Output() audioLevelChange = new EventEmitter<number>();

  audioAnalyser: AudioAnalyser | undefined;
  isPlaying: boolean = false;

  constructor(
    private audioService: AudioService,
    private audioPlayer: AudioPlayerService
  ) {}

  ngAfterViewInit() {
    this.startAnalyser().catch(console.error);
    this.audioPlayer.$playing.subscribe(playing => {
      this.isPlaying = playing;
      console.log("isPlaying value in ngAfterViewInit:", this.isPlaying);
    });
  }

  ngOnChanges(changes: SimpleChanges) {
    if (Object.hasOwn(changes, "state") && this.btn) {
      switch (changes["state"].currentValue) {
        case MicState.ACTIVE:
          this.mainLoop();
          break;
        case MicState.PENDING:
          this.btn.nativeElement.style.boxShadow = `var(--tw-ring-inset) 0 0 0 calc(0px + var(--tw-ring-offset-width)) var(--tw-ring-color)`;
          break;
        case MicState.DISABLED:
          this.btn.nativeElement.style.boxShadow = `var(--tw-ring-inset) 0 0 0 calc(24px + var(--tw-ring-offset-width)) var(--tw-ring-color)`;
          break;
      }
    }
  }

  async startAnalyser() {
    this.audioAnalyser = new AudioAnalyser(await this.audioService.getMicInput(), 4, 0.001);
  }

  mainLoop() {
    if (this.state === MicState.ACTIVE && this.audioAnalyser) {
      const raw_level = this.audioAnalyser.getAudioLevel();
      const level = (32 - (raw_level * this.btn.nativeElement.clientHeight) / 3).toFixed(2);
      this.btn.nativeElement.style.boxShadow = `var(--tw-ring-inset) 0 0 0 calc(${level}px + var(--tw-ring-offset-width)) var(--tw-ring-color)`;
      window.requestAnimationFrame(this.mainLoop.bind(this));
    }
  }

  buttonStateClasses() {
    switch (this.state) {
      case MicState.PENDING:
        return "tw-ring-[24px] tw-bg-emerald-300 tw-ring-white tw-text-emerald-900";
      case MicState.ACTIVE:
        return "tw-bg-emerald-300 tw-ring-white tw-text-emerald-700";
      case MicState.DISABLED:
        return "tw-ring-[24px] tw-bg-emerald-700 tw-ring-emerald-900 tw-text-emerald-900";
      default:
        console.warn("Mic state not set for mic button!");
        return "tw-transition tw-duration-75 tw-ring-0 tw-bg-white tw-ring-emerald-300 tw-text-emerald-900";
    }
  }

  handleAudioLevelChange(level: number) {
    this.audioLevelChange.emit(level);
  }

  protected readonly MicState = MicState;
}
