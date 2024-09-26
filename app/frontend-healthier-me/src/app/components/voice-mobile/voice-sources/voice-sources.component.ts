import { Component, Input, OnInit } from "@angular/core";
import { CarouselModule } from "primeng/carousel";
import { AccordionModule } from "primeng/accordion";
import { MessageSource } from "../../../types/message.type";
import { Panel, PanelModule } from "primeng/panel";

@Component({
  selector: "app-voice-sources",
  standalone: true,
  imports: [CarouselModule, AccordionModule, PanelModule],
  templateUrl: "./voice-sources.component.html",
  styleUrls: ["./voice-sources.component.css"]
})
export class VoiceSourcesComponent implements OnInit {
  testSources = [
    {
      title: "Lead Healthy and Happy Lives with These Health Tips",
      description: "DESCRIPTION",
      cover_image_url: "https://ch-api.healthhub.sg/api/public/content/5e1a87e404c44a26ae253d77976e630a?v=26491741&t=w347",
      url: "https://www.healthhub.sg/live-healthy/smoking-alcohol-and-drugs---why-teens-get-hooked-on-this-triple-threat"
    },
    {
      title: "Healthy Living: Ways to Live Healthy and Stay Healthy",
      description: "DESCRIPTION",
      cover_image_url: "https://ch-api.healthhub.sg/api/public/content/5e1a87e404c44a26ae253d77976e630a?v=26491741&t=w347",
      url: "https://www.healthhub.sg/live-healthy/smoking-alcohol-and-drugs---why-teens-get-hooked-on-this-triple-threat"
    },
    {
      title: "How to Stay Motivated and Lead a Healthy Lifestyle",
      description: "DESCRIPTION",
      cover_image_url: "https://ch-api.healthhub.sg/api/public/content/5e1a87e404c44a26ae253d77976e630a?v=26491741&t=w347",
      url: "https://www.healthhub.sg/live-healthy/smoking-alcohol-and-drugs---why-teens-get-hooked-on-this-triple-threat"
    }
  ];

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
