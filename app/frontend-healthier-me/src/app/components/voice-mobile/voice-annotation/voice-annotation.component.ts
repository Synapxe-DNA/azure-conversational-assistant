import { Component } from "@angular/core";
import { ButtonModule } from "primeng/button";
import { DialogModule } from "primeng/dialog";
import { FormsModule } from "@angular/forms";

@Component({
  selector: "app-voice-annotation",
  standalone: true,
  imports: [ButtonModule, DialogModule, FormsModule],
  templateUrl: "./voice-annotation.component.html",
  styleUrls: ["./voice-annotation.component.css"],
})
export class VoiceAnnotationComponent {
  displayModal: boolean = false;
  feedback: string = "";

  submitFeedback(rating: number) {
    console.log("Rating selected:", rating);
    this.displayModal = true;
  }
}
