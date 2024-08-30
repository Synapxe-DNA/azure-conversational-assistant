import { AfterViewInit, Component, ElementRef, Input, OnInit, ViewChild } from "@angular/core";
import { Message } from "../../../types/message.type";
import { MicState } from "../../../types/mic-state.type";
import { AudioAnalyser } from "../../../utils/audio-analyser";
import { AudioService } from "../../../services/audio/audio.service";
import { MarkdownComponent } from "../../markdown/markdown.component";
import { AudioPlayerService } from "../../../services/audio-player/audio-player.service";

@Component({
  selector: "app-voice-message",
  standalone: true,
  imports: [MarkdownComponent],
  templateUrl: "./voice-message.component.html",
  styleUrl: "./voice-message.component.css"
})
export class VoiceMessageComponent implements AfterViewInit, OnInit {
  @Input() message?: Message;
  @Input() state?: string;
  @Input() level?: number;
  audioAnalyser: AudioAnalyser | undefined;
  private animationFrameId: number | null = null;
  @ViewChild("box") box!: ElementRef<HTMLDivElement>;

  constructor(
    private audioService: AudioService,
    private audioPlayerService: AudioPlayerService
  ) {}

  ngOnInit(): void {}

  ngAfterViewInit(): void {
    this.startAnalyser().catch(console.error);
    this.audioPlayerService.$playing.subscribe(isPlaying => {
      if (isPlaying) {
        this.mainLoop();
      } else {
        this.stopLoop();
        this.box.nativeElement.style.boxShadow = `0 0 0px 0px rgb(243,244,246)`;
      }
    });
  }

  async startAnalyser() {
    this.audioAnalyser = new AudioAnalyser(await this.audioService.getMicInput(), 4, 0.001);
  }

  mainLoop() {
    if (this.audioAnalyser) {
      const raw_level = this.audioAnalyser.getAudioLevel();
      let adjusted_level = Math.round(Math.max(0, Math.min(1, raw_level * 4)) * 10) / 10;
      const level = Math.floor(40 * adjusted_level);
      this.box.nativeElement.style.boxShadow = `0 0 ${level}px ${level}px rgb(243,244,246)`;
      this.animationFrameId = window.requestAnimationFrame(this.mainLoop.bind(this));
    }
  }

  stopLoop() {
    if (this.animationFrameId !== null) {
      window.cancelAnimationFrame(this.animationFrameId); // AnimationFrame needs to be cancelled
      this.animationFrameId = null;
    }
  }
}
