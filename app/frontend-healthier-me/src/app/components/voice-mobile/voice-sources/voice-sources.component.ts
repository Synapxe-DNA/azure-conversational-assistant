import { Component, Input, OnInit } from "@angular/core";
import { CarouselModule } from "primeng/carousel";
import { AccordionModule } from "primeng/accordion";
import { MessageSource } from "../../../types/message.type";

// const sources = [
//   {
//     "title": "TITLE",
//     "description": "DESCRIPTION",
//     "cover_image_url": "https://ch-api.healthhub.sg/api/public/content/5e1a87e404c44a26ae253d77976e630a?v=26491741&t=w347",
//     "url": "https://www.healthhub.sg/live-healthy/smoking-alcohol-and-drugs---why-teens-get-hooked-on-this-triple-threat"
//   },
//   {
//     "title": "TITLE",
//     "description": "DESCRIPTION",
//     "cover_image_url": "https://ch-api.healthhub.sg/api/public/content/5e1a87e404c44a26ae253d77976e630a?v=26491741&t=w347",
//     "url": "https://www.healthhub.sg/live-healthy/smoking-alcohol-and-drugs---why-teens-get-hooked-on-this-triple-threat"
//   },
//   {
//     "title": "TITLE",
//     "description": "DESCRIPTION",
//     "cover_image_url": "https://ch-api.healthhub.sg/api/public/content/5e1a87e404c44a26ae253d77976e630a?v=26491741&t=w347",
//     "url": "https://www.healthhub.sg/live-healthy/smoking-alcohol-and-drugs---why-teens-get-hooked-on-this-triple-threat"
//   },
//   {
//     "title": "TITLE",
//     "description": "DESCRIPTION",
//     "cover_image_url": "https://ch-api.healthhub.sg/api/public/content/5e1a87e404c44a26ae253d77976e630a?v=26491741&t=w347",
//     "url": "https://www.healthhub.sg/live-healthy/smoking-alcohol-and-drugs---why-teens-get-hooked-on-this-triple-threat"
//   },
// ]

const sources: MessageSource[] = [];

@Component({
  selector: "app-voice-sources",
  standalone: true,
  imports: [CarouselModule, AccordionModule],
  templateUrl: "./voice-sources.component.html",
  styleUrl: "./voice-sources.component.css",
})
export class VoiceSourcesComponent implements OnInit {
  responsiveOptions: any[] | undefined;

  @Input() sources: MessageSource[] = sources;

  ngOnInit(): void {
    this.responsiveOptions = [
      {
        breakpoint: "768px",
        numVisible: 1,
        numScroll: 1,
      },
    ];
  }
}
