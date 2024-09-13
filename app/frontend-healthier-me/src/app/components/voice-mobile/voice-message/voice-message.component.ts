import { AfterViewInit, Component, ElementRef, Input, OnInit, ViewChild } from "@angular/core";
import { Message } from "../../../types/message.type";
import { MicState } from "../../../types/mic-state.type";
import { AudioAnalyser } from "../../../utils/audio-analyser";
import { AudioService } from "../../../services/audio/audio.service";
import { MarkdownComponent } from "../../markdown/markdown.component";
import { AudioPlayerService } from "../../../services/audio-player/audio-player.service";
import { FormsModule } from "@angular/forms";
import { CommonModule } from "@angular/common";

@Component({
  selector: "app-voice-message",
  standalone: true,
  imports: [MarkdownComponent, FormsModule, CommonModule],
  templateUrl: "./voice-message.component.html",
  styleUrl: "./voice-message.component.css"
})
export class VoiceMessageComponent implements AfterViewInit, OnInit {
  @Input() message?: Message;
  @Input() state?: string;
  @Input() level?: number;
  @Input() fontSize: number = 16; // Default value
  audioAnalyser: AudioAnalyser | undefined;
  private animationFrameId: number | null = null;
  @ViewChild("box") box!: ElementRef<HTMLDivElement>;

  constructor(
    private audioService: AudioService,
    private audioPlayerService: AudioPlayerService
  ) {}

  ngOnInit(): void {
    // Retrieve the font size from local storage (if it exists)
    const savedFontSize = localStorage.getItem("fontSize");
    if (savedFontSize) {
      this.fontSize = Number(savedFontSize);
    }
  }

  ngAfterViewInit(): void {
    this.audioPlayerService.getAudioStream().subscribe(v => {
      if (v) {
        this.audioAnalyser = new AudioAnalyser(v as MediaStream, 9, 0.3);
        this.mainLoop();
      }
    });
  }

  mainLoop() {
    const raw_level = this.audioAnalyser!.getAudioLevel();
    const level = Math.floor(40 * raw_level);
    this.box.nativeElement.style.boxShadow = `0 0 ${level}px ${level}px rgb(243,244,246)`;
    this.animationFrameId = window.requestAnimationFrame(this.mainLoop.bind(this));
  }

  onFontSizeChange() {
    // Save the font size in local storage whenever it changes
    localStorage.setItem("fontSize", this.fontSize.toString());
  }
}
