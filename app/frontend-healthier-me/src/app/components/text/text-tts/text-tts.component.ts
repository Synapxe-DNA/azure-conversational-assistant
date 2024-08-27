import { Component, Input } from "@angular/core";
import { Button } from "primeng/button";
import { EndpointService } from "../../../services/endpoint/endpoint.service";
import { AudioPlayerService } from "../../../services/audio-player/audio-player.service";

@Component({
  selector: "app-text-tts",
  standalone: true,
  imports: [Button],
  templateUrl: "./text-tts.component.html",
  styleUrl: "./text-tts.component.css",
})
export class TextTtsComponent {
  @Input() message!: string;

  constructor(
    private endpointService: EndpointService,
    private audioPlayerService: AudioPlayerService,
  ) {}

  async textToSpeech() {
    try {
      const audioSubject = await this.endpointService.textToSpeech(
        this.message,
      );

      audioSubject.subscribe({
        next: (blob) => {
          if (blob) {
            this.audioPlayerService.play(blob);
          }
        },
        error: (error) => {
          console.error("Error:", error);
        },
      });
    } catch (error) {
      console.error("Failed to get BehaviorSubject:", error);
    }
  }
}
