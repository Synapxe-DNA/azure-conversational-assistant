import { Component, Input, OnInit } from '@angular/core';
import { CarouselModule } from 'primeng/carousel';
import { AccordionModule } from 'primeng/accordion';
import { MessageSource } from '../../../types/message.type';

@Component({
  selector: 'app-voice-sources',
  standalone: true,
  imports: [
    CarouselModule,
    AccordionModule,
  ],
  templateUrl: './voice-sources.component.html',
  styleUrl: './voice-sources.component.css'
})
export class VoiceSourcesComponent implements OnInit{

  responsiveOptions: any[] | undefined;

  @Input() sources!: MessageSource[];

  ngOnInit(): void {
    this.responsiveOptions = [
      {
          breakpoint: '768px',
          numVisible: 1,
          numScroll: 1
      }
  ];
}
}
