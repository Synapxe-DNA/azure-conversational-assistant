import {
  AfterViewInit,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnInit,
  Output,
  QueryList,
  ViewChild,
  ViewChildren,
} from "@angular/core";
import { CommonModule } from "@angular/common";
import { AudioService } from "../../services/audio/audio.service";
import { AudioAnalyser } from "../../utils/audio-analyser";
import { AudioPlayerService } from "../../services/audio-player/audio-player.service";

@Component({
  selector: "app-waveform",
  standalone: true,
  imports: [CommonModule],
  templateUrl: "./waveform.component.html",
  styleUrl: "./waveform.component.css",
})
export class WaveformComponent implements AfterViewInit {
  @Input() bars: number = 8;
  @Input() barWidth: string = "3px";
  @Input() barHeight: string = "5px";
  @Input() containerHeight: string = "8rem";
  @Input() containerGap: string = "1rem";
  @Input() heightScalingFactor: number = 0.5;

  @ViewChild("container") container!: ElementRef;
  @ViewChildren("bar") levelBars!: QueryList<ElementRef>;

  @Output() audioLevelChange = new EventEmitter<number>();

  barHeights: number[] = [];

  audioAnalyser: AudioAnalyser | undefined;

  constructor(
    private audioService: AudioService,
    private audioPlayerService: AudioPlayerService,
  ) {}

  ngAfterViewInit() {
    this.barHeights = new Array<number>(this.bars).fill(0);
    this.startAnalyser()
      .then(() => {
        this.mainLoop();
      })
      .catch(console.error);
  }

  async startAnalyser() {
    this.audioPlayerService.getAudioStream().subscribe((v) => {
      if (v) {
        // One more bar is added so that the "highest" frequency bar is attainable with regular voice
        this.audioAnalyser = new AudioAnalyser(
          v as MediaStream,
          this.bars + 1,
          0.3,
        );
      }
    });
  }

  mainLoop() {
    try {
      if (this.audioAnalyser) {
        const barHeights = this.audioAnalyser.getFrequency();
        let averageHeight = 0;

        this.levelBars.forEach((b, index) => {
          const heightMultiplier =
            this.heightScalingFactor *
            (1 + Math.sin((index / barHeights.length) * Math.PI));
          const barHeight =
            barHeights[index] *
            heightMultiplier *
            this.container.nativeElement.clientHeight;
          b.nativeElement.style.height = `${barHeight}px`;
          averageHeight += barHeight;
        });

        averageHeight /= this.bars;
        this.audioLevelChange.emit(averageHeight);
      }
    } catch (e) {
      console.error(e);
    }

    window.requestAnimationFrame(this.mainLoop.bind(this));
  }

  protected readonly Array = Array;
}
