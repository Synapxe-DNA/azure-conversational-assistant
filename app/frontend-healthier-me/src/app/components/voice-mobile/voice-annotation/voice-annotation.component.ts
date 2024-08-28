import { ConvoBrokerService } from "./../../../services/convo-broker/convo-broker.service";
import { Component } from "@angular/core";
import { ButtonModule } from "primeng/button";
import { DialogModule } from "primeng/dialog";
import { FormsModule } from "@angular/forms";
import { Feedback } from "../../../types/feedback.type";

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
  remarks: string = "";
  rating: Number = -1;
  selectedCategory: string | null = "Others";

  constructor(private convoBrokerService: ConvoBrokerService) {}

  showDialog(rating: Number) {
    this.displayModal = true;
    this.rating = rating;
  }

  selectCategory(category: string) {
    this.selectedCategory = category;
    console.log(`Selected category: ${category}`);
  }

  submitFeedback() {
    const feedback: Feedback = {
      label: this.rating === 0 ? "positive" : "negative",
      category: this.selectedCategory!,
      remarks: this.remarks,
      chat_history: [],
      profile_id: "",
      datetime: new Date().toLocaleString("en-GB", {
        timeZone: "Asia/Singapore",
      }),
    };

    // log the fields of the feedback object
    console.log("Feedback label:", feedback.label);
    console.log("Feedback category:", feedback.category);
    console.log("Feedback remarks:", feedback.remarks);
    console.log("Feedback date:", feedback.datetime);

    // Handle the feedback submission logic here
    this.displayModal = false;
    this.confirmationModal = true; // Show the confirmation modal
    this.remarks = ""; // Reset the feedback field
  }
}
