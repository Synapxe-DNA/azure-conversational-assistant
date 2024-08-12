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
      const responseBS = await this.endpointService.textToSpeech(this.message);
      responseBS.subscribe({
        next: (response) => {
          if (response) {
            console.log("text-tts.component: textToSpeech() 2");
            //const audioBlob = this.base64ToBlob(response.audio);
            //console.log("audioBlob:", audioBlob);
            //this.audioPlayerService.play(audioBlob);
          }
        },
        error: (err) => console.error("TTS Error:", err),
      });
    } catch (err) {
      console.error("TTS Error:", err);
    }
  }

  private base64ToBlob(
    base64String: string,
    contentType: string = "audio/wav",
  ): Blob {
    try {
      const base64Data = base64String.replace(/^data:.+;base64,/, "");
      const binaryString = atob(base64Data);
      const binaryLen = binaryString.length;
      const bytes = new Uint8Array(binaryLen);

      for (let i = 0; i < binaryLen; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }

      return new Blob([bytes], { type: contentType });
    } catch (error) {
      console.error("Error converting base64 to Blob:", error);
      throw error;
    }
  }
}
