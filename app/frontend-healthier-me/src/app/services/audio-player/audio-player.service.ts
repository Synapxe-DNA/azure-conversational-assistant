import { Injectable } from "@angular/core";
import { BehaviorSubject } from "rxjs";

interface HTMLMediaElementWithCaptureStream extends HTMLMediaElement {
  captureStream(): MediaStream;
}

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

  private audioElement: HTMLMediaElementWithCaptureStream =
    new Audio() as HTMLMediaElementWithCaptureStream;

  $stream: BehaviorSubject<MediaStream | null> =
    new BehaviorSubject<MediaStream | null>(null);
  $playing: BehaviorSubject<boolean> = new BehaviorSubject<boolean>(false);

  constructor() {
    this.audioElement.addEventListener("ended", () => {
      this.$playing.next(false);
    });
  }

  getAudioStream(): BehaviorSubject<MediaStream | null> {
    return this.$stream;
  }

  /**
   * Method to play an audio from a blob
   * @param blob {Blob}
   */
  play(blob: Blob): void {
    this.audioElement.pause();
    this.audioElement.src = URL.createObjectURL(blob);
    this.audioElement
      .play()
      .then(() => {
        this.$playing.next(true);
        this.$stream.next(this.audioElement.captureStream());
      })
      .catch(console.error);
  }

  stop(): void {
    this.audioElement.pause();
    this.$playing.next(false);
  }
}
