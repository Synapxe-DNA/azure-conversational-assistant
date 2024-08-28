import { Component, Input, OnInit } from "@angular/core";
import { CarouselModule } from "primeng/carousel";
import { AccordionModule } from "primeng/accordion";
import { MessageSource } from "../../../types/message.type";

@Component({
  selector: "app-voice-sources",
  standalone: true,
  imports: [CarouselModule, AccordionModule],
  templateUrl: "./voice-sources.component.html",
  styleUrls: ["./voice-sources.component.css"]
})
export class VoiceSourcesComponent implements OnInit {
  responsiveOptions: any[] | undefined;
  hoveredImageUrl: string | null = null; // Variable to hold the hovered image URL

  @Input() sources: MessageSource[] = [];
  imgUrl: string = "assets/healthhub-logo.png"; // Updated path

  ngOnInit(): void {
    this.responsiveOptions = [
      {
        breakpoint: "768px",
        numVisible: 1,
        numScroll: 1
      }
    ];
  }

  // Method to get the image URL
  getImageUrl(coverImageUrl: string | null): string {
    // Check if coverImageUrl is 'None' or falsy and return the fallback image URL
    return coverImageUrl && coverImageUrl !== "None" ? coverImageUrl : this.imgUrl;
  }

  // Method to log the image URL
  logImageUrl(url: string | null): void {
    if (url && url !== "None") {
      this.hoveredImageUrl = url; // Set the hovered image URL
    }
  }

  // // Method to clear the log
  // clearLog(): void {
  //   this.hoveredImageUrl = null; // Clear the hovered image URL
  // }
}
