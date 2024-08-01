import { Component, Input } from "@angular/core";
import { Clipboard } from "@angular/cdk/clipboard";
import { Message } from "../../../types/message.type";
import { LucideAngularModule } from "lucide-angular";

@Component({
  selector: "app-text-clipboard",
  standalone: true,
  imports: [LucideAngularModule],
  templateUrl: "./text-clipboard.component.html",
  styleUrl: "./text-clipboard.component.css",
})
export class TextClipboardComponent {
  @Input() message!: Message;

  constructor(private clipboard: Clipboard) {}

  copyToClipboard() {
    if (this.message && this.message.message) {
      this.clipboard.copy(this.message.message);
    }
  }
}
