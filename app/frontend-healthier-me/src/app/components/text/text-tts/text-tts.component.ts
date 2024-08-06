import { Component, Input } from "@angular/core";
import { Button } from "primeng/button";

@Component({
  selector: "app-text-tts",
  standalone: true,
  imports: [Button],
  templateUrl: "./text-tts.component.html",
  styleUrl: "./text-tts.component.css",
})
export class TextTtsComponent {
  @Input() message!: string;

  speechToText() {
    // Implement speech to text functionality here
    console.log("Speech to Text");
  }
}
