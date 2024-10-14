import { Component, Input } from "@angular/core";
import { MessageSource } from "../../../types/message.type";
import { CommonModule } from "@angular/common";

@Component({
  selector: "app-text-source",
  standalone: true,
  imports: [CommonModule],
  templateUrl: "./text-source.component.html",
  styleUrl: "./text-source.component.css"
})
export class TextSourceComponent {
  @Input() sources?: MessageSource[];
  @Input() display?: boolean;

  imgUrl: string = "assets/healthhub-logo.png";

  // Method to get the image URL
  getImageUrl(coverImageUrl: string | null): string {
    // Check if coverImageUrl is 'None' or falsy and return the fallback image URL
    return coverImageUrl && coverImageUrl !== "None" ? coverImageUrl : this.imgUrl;
  }
}
