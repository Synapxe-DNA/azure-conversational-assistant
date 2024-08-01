import {
  AfterViewInit,
  Component,
  ElementRef,
  Input,
  OnInit,
  QueryList,
  ViewChild,
  ViewChildren,
} from "@angular/core"
import { AudioService } from "../../services/audio/audio.service"
import { AudioAnalyser } from "../../utils/audio-analyser"

@Component({
  selector: "app-waveform",
  standalone: true,
  imports: [],
  templateUrl: "./waveform.component.html",
  styleUrl: "./waveform.component.css",
})
export class WaveformComponent implements AfterViewInit {
  @Input() bars!: number
  stream: MediaStream | undefined

  @ViewChild("container") container!: ElementRef
  @ViewChildren("bar") levelBars!: QueryList<ElementRef>

  barHeights: number[] = []

  audioAnalyser: AudioAnalyser | undefined

  constructor(private audioService: AudioService) {}

  ngAfterViewInit() {
    this.barHeights = new Array<number>(this.bars).fill(0)
    this.startAnalyser()
      .then(() => {
        this.mainLoop()
      })
      .catch(console.error)
  }

  async startAnalyser() {
    // TODO this should be done from user input
    this.stream = await this.audioService.getMicInput()

    // One more bar is added so that the "highest" frequency bar is attainable with regular voice
    this.audioAnalyser = new AudioAnalyser(
      this.stream as MediaStream,
      this.bars + 1, 0.9
    )
  }

  mainLoop() {
    try {
      if (this.audioAnalyser) {
        const barHeights = this.audioAnalyser.getFrequency()
        this.levelBars.forEach((b, index) => {
          // Scale height of bar based on audio levels.
          // Scaled for higher mid-tones
          b.nativeElement.style.height = `${barHeights[index] * (1 + Math.sin((index / barHeights.length) * Math.PI)) * this.container.nativeElement.clientHeight}px`
        })
      }
    } catch (e) {
      console.error(e)
    }

    window.requestAnimationFrame(this.mainLoop.bind(this))
  }

  protected readonly Array = Array
}
