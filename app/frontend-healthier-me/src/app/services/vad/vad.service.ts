import {Injectable} from '@angular/core';
import {BehaviorSubject, Observable, repeat, retry, Subject} from "rxjs";
import {VoiceActivity} from "../../types/voice-activity.type";

@Injectable({
  providedIn: 'root'
})
export class VadService {

  private endTimeout:number = 0
  private $speech:Subject<void> = new Subject<void>()
  private recognition:SpeechRecognition



  constructor(
  ) {

    if(Object.hasOwn(window, "SpeechRecognition")){
      this.recognition = new SpeechRecognition()
    } else if (Object.hasOwn(window, "webkitSpeechRecognition")){
      this.recognition = new webkitSpeechRecognition()
    } else {
      // TODO fallback strategy for speech recognition
      throw new Error("Fallback VAD not implemented!")
    }

    this.configSpeechRecognition()
  }

  private configSpeechRecognition(){
    this.recognition.continuous = true
    this.recognition.interimResults = true
    this.recognition.onresult = () => {
      this.$speech.next()
    }
    this.recognition.start()
  }

  start():Observable<VoiceActivity>{

    const vadState = new BehaviorSubject<VoiceActivity>(VoiceActivity.End)

    this.$speech.subscribe({
      next: (res)=>{

        if(vadState.value!==VoiceActivity.Start){
          // User has started talking
          vadState.next(VoiceActivity.Start)
        }

        // User has said something
        clearTimeout(this.endTimeout)
        this.endTimeout = setTimeout(() => {
          vadState.next(VoiceActivity.End)
        }, 1000) // fire "end" after 1.0s of inactivity
      },
      error: (e:Error) => {console.error(e)},
      complete: ()=>{console.log("done")}
    })

    return vadState.asObservable()

  }

}
