import {
  AfterViewInit,
  Component,
  ElementRef,
  Input,
  OnInit,
  ViewChild,
} from "@angular/core";
import { Message } from "../../../types/message.type";
import { MicState } from "../../../types/mic-state.type";
import { AudioAnalyser } from "../../../utils/audio-analyser";
import { AudioService } from "../../../services/audio/audio.service";
import { MarkdownComponent } from "../../markdown/markdown.component";

@Component({
  selector: "app-voice-message",
  standalone: true,
  imports: [MarkdownComponent],
  templateUrl: "./voice-message.component.html",
  styleUrl: "./voice-message.component.css",
})
export class VoiceMessageComponent implements AfterViewInit, OnInit {
  @Input() message?: Message;
  @Input() state?: string;
  audioAnalyser: AudioAnalyser | undefined;
  @ViewChild("box") box!: ElementRef<HTMLDivElement>;

  constructor(private audioService: AudioService) {}

  ngOnInit(): void {}

  ngAfterViewInit(): void {
    this.startAnalyser().catch(console.error);
  }

  async startAnalyser() {
    this.audioAnalyser = new AudioAnalyser(
      await this.audioService.getMicInput(),
      4,
      0.001,
    );
  }

  mainLoop() {
    if (this.audioAnalyser) {
      const raw_level = this.audioAnalyser.getAudioLevel();
      const level = (
        32 -
        (raw_level * this.box.nativeElement.clientHeight) / 3
      ).toFixed(2);
      this.box.nativeElement.style.boxShadow = `var(--tw-ring-inset) 0 0 0 calc(${level}px + var(--tw-ring-offset-width)) var(--tw-ring-color)`;
      window.requestAnimationFrame(this.mainLoop.bind(this));
    }
  }
}
