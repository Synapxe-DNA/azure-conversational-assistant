import { Injectable } from "@angular/core";
import { BehaviorSubject, Observable, repeat, retry, Subject } from "rxjs";
import { VoiceActivity } from "../../types/voice-activity.type";
import { AudioService } from "../audio/audio.service";

@Injectable({
  providedIn: "root"
})
export class VadService {
  private endTimeout: number = 0;
  private $speech: Subject<void> = new Subject<void>();
  private recognition!: SpeechRecognition;

  // VAD is active during text mode; to prevent the constant blinking of the "mic" icon on mac devices,
  // the user mic will continuously be referenced.
  private __mic!: Promise<MediaStream>;

  constructor(private audio: AudioService) {
    // this.__mic = this.audio.getMicInput();
    // this.configSpeechRecognition();
  }

  /**
   * Method to start speech recognition
   * @private
   */
  private configSpeechRecognition() {
    if (Object.hasOwn(window, "SpeechRecognition")) {
      this.recognition = new SpeechRecognition();
    } else if (Object.hasOwn(window, "webkitSpeechRecognition")) {
      this.recognition = new webkitSpeechRecognition();
    } else {
      // TODO fallback strategy for speech recognition
      throw new Error("Fallback VAD not implemented!");
    }

    this.recognition.continuous = true;
    this.recognition.interimResults = true;
    this.recognition.onresult = () => {
      this.$speech.next();
    };
    this.recognition.onaudiostart = () => {
      // console.log("VAD Start!");
    };
    this.recognition.onaudioend = () => {
      // console.warn("VAD Ended! Starting new VAD session");
      this.configSpeechRecognition();
    };
    this.recognition.onerror = () => {
      // console.warn("VAD Error! Restarting VAD session");
      this.configSpeechRecognition();
    };
    // this.recognition.start();
  }

  startRecognition() {
    this.recognition.start();
  }

  stopRecognition() {
    this.recognition.stop();
  }
   
  

  /**
   * Method to start VAD globally
   */
  start(): Observable<VoiceActivity> {
    const vadState = new BehaviorSubject<VoiceActivity>(VoiceActivity.End);

    this.$speech.subscribe({
      next: res => {
        if (vadState.value !== VoiceActivity.Start) {
          // User has started talking
          vadState.next(VoiceActivity.Start);
        }

        // User has said something
        clearTimeout(this.endTimeout);
        this.endTimeout = setTimeout(() => {
          vadState.next(VoiceActivity.End);
        }, 1000); // fire "end" after 1.0s of inactivity
      },
      error: (e: Error) => {
        console.error(e);
      },
      complete: () => {
        console.log("done");
      }
    });

    return vadState.asObservable();
  }
}
