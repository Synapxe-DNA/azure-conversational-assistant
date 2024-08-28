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
  confirmationModal: boolean = false;
  feedback: String = "";
  rating: Number = -1;
  selectedCategory: string | null = null;

  showDialog(rating: Number) {
    this.displayModal = true;
    this.rating = rating;
  }

  selectCategory(category: string) {
    this.selectedCategory = category;
    console.log(`Selected category: ${category}`);
  }

  submitFeedback() {
    // Handle the feedback submission logic here
    console.log("Feedback submitted:", this.feedback);
    this.displayModal = false;
    this.confirmationModal = true; // Show the confirmation modal
  }
}
