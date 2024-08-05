import { Component, Input } from "@angular/core";
import { Clipboard } from "@angular/cdk/clipboard";
import { Button } from "primeng/button";

@Component({
  selector: "app-text-clipboard",
  standalone: true,
  imports: [Button],
  templateUrl: "./text-clipboard.component.html",
  styleUrl: "./text-clipboard.component.css",
})
export class TextClipboardComponent {
  @Input() message!: string;

  constructor(private clipboard: Clipboard) {}

  copyToClipboard() {
    this.clipboard.copy(this.message);
  }
}
