import { Injectable } from "@angular/core";
import { BehaviorSubject } from "rxjs";

@Injectable({
  providedIn: "root",
})
export class AudioPlayerService {
  /**
   * This service is responsible for playing audio, from TTS and voice chat.
   *
   * Assumptions:
   * - Only one audio can be played at one time.
   */

  private audioElement: HTMLAudioElement = new Audio();

  $playing: BehaviorSubject<boolean> = new BehaviorSubject<boolean>(false);

  constructor() {
    this.audioElement.addEventListener("ended", () => {
      this.$playing.next(false);
    });
  }

  /**
   * Method to play an audio from a blob
   * @param blob {Blob}
   */
  play(blob: Blob): void {
    this.audioElement.pause();
    this.audioElement.src = URL.createObjectURL(blob);
    this.$playing.next(true);
    this.audioElement.play().catch(console.error);
  }
}
