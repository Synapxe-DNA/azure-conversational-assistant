import { Component, Input } from "@angular/core";
import { Message } from "../../../types/message.type";
import { TextSourceComponent } from "../text-source/text-source.component";
import { TextTtsComponent } from "../text-tts/text-tts.component";
import { TextClipboardComponent } from "../text-clipboard/text-clipboard.component";
import { TextShowSourceComponent } from "../text-show-source/text-show-source.component";

@Component({
  selector: "app-text-system",
  standalone: true,
  imports: [TextSourceComponent, TextTtsComponent, TextClipboardComponent, TextShowSourceComponent],
  templateUrl: "./text-system.component.html",
  styleUrl: "./text-system.component.css"
})
export class TextSystemComponent {
  @Input() message!: Message;
  display: boolean = false;

  toggleDisplay(display: boolean) {
    this.display = display;
  }
}
