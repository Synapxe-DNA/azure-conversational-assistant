import {AfterViewInit, Component, OnInit} from "@angular/core";
import {PreferenceService} from "../../services/preference/preference.service";
import {WaveformComponent} from "../waveform/waveform.component";
import {MicrophoneButtonComponent} from "../microphone-button/microphone-button.component";
import {MicState} from "../../types/mic-state.type";
import {SecondaryButtonComponent} from "../secondary-button/secondary-button.component";
import {LucideAngularModule} from "lucide-angular";
import {Button} from "primeng/button";
import {OverlayPanelModule} from "primeng/overlaypanel";
import {InputSwitchChangeEvent, InputSwitchModule} from "primeng/inputswitch";
import {ChatMode} from "../../types/chat-mode.type";
import {FormsModule} from "@angular/forms";
import {AudioRecorder} from "../../utils/audio-recorder";
import {VadService} from "../../services/vad/vad.service";
import {AudioService} from "../../services/audio/audio.service";
import {VoiceActivity} from "../../types/voice-activity.type";
import {BehaviorSubject} from "rxjs";

@Component({
  selector: "app-voice",
  standalone: true,
  imports: [
    WaveformComponent,
    MicrophoneButtonComponent,
    SecondaryButtonComponent,
    LucideAngularModule,
    Button,
    OverlayPanelModule,
    InputSwitchModule,
    FormsModule,
  ],
  templateUrl: "./voice.component.html",
  styleUrl: "./voice.component.css",
})
export class VoiceComponent implements OnInit, AfterViewInit{

  private isUserTurn: BehaviorSubject<boolean> = new BehaviorSubject<boolean>(true)
  private recorder: AudioRecorder | undefined

  micState: MicState = MicState.PENDING;

  voiceInterrupt:boolean = false
  voiceDetectStart:boolean = false
  voiceDetectEnd:boolean = false

  constructor(
    private preference: PreferenceService,
    private vad: VadService,
    private audio: AudioService
  ) {
  }

  ngOnInit() {
    this.preference.$voiceDetectInterrupt.subscribe(v => {this.voiceInterrupt = v})
    this.preference.$voiceDetectStart.subscribe(v => this.voiceDetectStart=v)
    this.preference.$voiceDetectEnd.subscribe(v => this.voiceDetectEnd=v)
  }

  ngAfterViewInit() {
    this.initVoiceChat().catch(console.error)
  }

  private async initVoiceChat(){

    this.recorder = new AudioRecorder(await this.audio.getMicInput())

    this.vad.start().subscribe({
      next: (s) => {

        switch (s){
          case VoiceActivity.Start:
            if(this.isUserTurn.value && this.voiceDetectStart && this.micState===MicState.PENDING){
              this.handleStart()
            }
            break
          case VoiceActivity.End:
            if(this.isUserTurn.value && this.micState===MicState.ACTIVE && this.voiceDetectEnd){
              this.handleStop()
            }
        }
      }
    })

  }

  handleStart() {
    this.micState = MicState.ACTIVE
    this.recorder!.start()
    console.log("Starting")
  }

  handleStop(){
    this.micState = MicState.DISABLED
    this.isUserTurn.next(false)
    this.recorder!.stop()
      .then(r => {
        console.log(r)
        // TODO handle submission of voice recoding and handling of response here!

        // Downloading to test
        // Generate a URL for the Blob
        const url = window.URL.createObjectURL(r.data);

        // Create a download link
        const downloadLink = document.createElement('a');
        downloadLink.style.display = 'none';
        downloadLink.href = url;
        downloadLink.download = 'audio.webm';
        document.body.appendChild(downloadLink);
        downloadLink.click();

      // Automatically click the download link to trigger the download
      })
      .then(()=>{
        // Simulate time while processing response
        setTimeout(()=>{
          this.micState = MicState.PENDING
          this.isUserTurn.next(true)
        }, 500)
      })
  }

  handleMicButtonClick(){
    switch (this.micState){
      case MicState.ACTIVE:
        this.handleStop()
        break
      case MicState.PENDING:
        this.handleStart()
        break
    }
  }

  prefChatModeToText():void{
    this.preference.setChatMode(ChatMode.Text)
  }

  prefVoiceInterrupt(e:InputSwitchChangeEvent){
    this.preference.setVoiceDetectInterrupt(e.checked)
  }

  prefVoiceStart(e:InputSwitchChangeEvent){
    this.preference.setVoiceDetectStart(e.checked)
  }

  prefVoiceEnd(e:InputSwitchChangeEvent){
    this.preference.setVoiceDetectEnd(e.checked)
  }
}
