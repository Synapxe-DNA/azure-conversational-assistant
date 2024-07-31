import {AfterViewInit, Component, ElementRef, EventEmitter, Input, OnChanges, Output, SimpleChanges,
  ViewChild
} from "@angular/core";
import {CommonModule} from "@angular/common";
import {LucideAngularModule} from "lucide-angular";
import {MicState} from "../../types/mic-state.type";
import {AudioService} from "../../services/audio/audio.service";
import {AudioAnalyser} from "../../utils/audio-analyser";

@Component({
  selector: "app-microphone-button",
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  templateUrl: "./microphone-button.component.html",
  styleUrls: ["./microphone-button.component.css"],
})
export class MicrophoneButtonComponent implements AfterViewInit, OnChanges {
  @Input() state!: MicState

  @ViewChild("btn") btn!: ElementRef<HTMLButtonElement>

  audioAnalyser: AudioAnalyser | undefined

  constructor(
    private audioService: AudioService
  ) {
  }

  ngAfterViewInit() {
    this.startAnalyser()
      .catch(console.error)
  }

  ngOnChanges(changes: SimpleChanges) {
    if(Object.hasOwn(changes, 'state') && this.btn){
      switch (changes['state'].currentValue){
        case MicState.ACTIVE:
          this.mainLoop()
          break
        case MicState.PENDING:
          this.btn.nativeElement.style.boxShadow = `var(--tw-ring-inset) 0 0 0 calc(0px + var(--tw-ring-offset-width)) var(--tw-ring-color)`
          break
        case MicState.DISABLED:
          this.btn.nativeElement.style.boxShadow = `var(--tw-ring-inset) 0 0 0 calc(24px + var(--tw-ring-offset-width)) var(--tw-ring-color)`
          break
      }
    }
  }

  async startAnalyser(){
    this.audioAnalyser = new AudioAnalyser(await this.audioService.getMicInput(), 4, 0.001)
  }

  mainLoop(){
    if(this.state===MicState.ACTIVE && this.audioAnalyser){
      const raw_level = this.audioAnalyser.getAudioLevel()
      const level = (32 - (raw_level * this.btn.nativeElement.clientHeight/3)) .toFixed(2)
      this.btn.nativeElement.style.boxShadow = `var(--tw-ring-inset) 0 0 0 calc(${level}px + var(--tw-ring-offset-width)) var(--tw-ring-color)`
      window.requestAnimationFrame(this.mainLoop.bind(this))
    }
  }

  buttonStateClasses() {
    switch (this.state) {
      case MicState.PENDING:
        return "tw-ring-0 tw-bg-white tw-ring-emerald-300 tw-text-emerald-900"
      case MicState.ACTIVE:
        return "tw-bg-white tw-ring-emerald-300 tw-text-emerald-700"
      case MicState.DISABLED:
        return "tw-ring-[24px] tw-bg-emerald-700 tw-ring-emerald-900 tw-text-emerald-900"
      default:
        console.warn("Mic state not set for mic button!")
        return "tw-transition tw-duration-75 tw-ring-0 tw-bg-white tw-ring-emerald-300 tw-text-emerald-900"
    }
  }

  protected readonly MicState = MicState;
}
