import { Component, EventEmitter, Input, Output } from "@angular/core";
import { Button } from "primeng/button";
import { MessageSource } from "../../../types/message.type";

@Component({
  selector: "app-text-show-source",
  standalone: true,
  imports: [Button],
  templateUrl: "./text-show-source.component.html",
  styleUrl: "./text-show-source.component.css",
})
export class TextShowSourceComponent {
  @Input() sources?: MessageSource[];
  @Output() display = new EventEmitter<boolean>();
  hidden: boolean = false;

  toggleDisplay() {
    this.hidden = !this.hidden;
    this.display.emit(this.hidden);
  }
}
