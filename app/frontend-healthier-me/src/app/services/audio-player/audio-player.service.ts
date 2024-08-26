import { Injectable } from "@angular/core";
import { BehaviorSubject } from "rxjs";

interface HTMLMediaElementWithCaptureStream extends HTMLMediaElement {
  captureStream(): MediaStream;
}

@Injectable({
  providedIn: "root"
})
export class AudioPlayerService {
  /**
   * This service is responsible for playing audio, from TTS and voice chat.
   *
   * Assumptions:
   * - Only one audio can be played at one time.
   */

  private audioElement: HTMLMediaElementWithCaptureStream = new Audio() as HTMLMediaElementWithCaptureStream;

  private queue: Blob[] = [];

  $stream: BehaviorSubject<MediaStream | null> = new BehaviorSubject<MediaStream | null>(null);
  $playing: BehaviorSubject<boolean> = new BehaviorSubject<boolean>(false);

  constructor() {
    this.audioElement.addEventListener("ended", () => {
      if (this.queue.length) {
        this.playNextInQueue();
      } else {
        // No more audio left
        this.$playing.next(false);
      }
    });
  }

  private playNextInQueue() {
    this.$playing.next(true);
    const blob = this.queue.shift()!;
    this.audioElement.src = URL.createObjectURL(blob);
    this.audioElement.play().then(() => {
      this.$stream.next(this.audioElement.captureStream());
    });
  }

  /**
   * Method to get the BehaviorSubject tracking the latest audio stream
   */
  getAudioStream(): BehaviorSubject<MediaStream | null> {
    return this.$stream;
  }

  /**
   * Method to play an audio from a blob
   * @param blob {Blob}
   */
  play(...blob: Blob[]): void {
    blob.forEach(b => this.queue.push(b));
    if (!this.$playing.value) {
      this.playNextInQueue();
    }
  }

  forcePlayAndReplace(blob: Blob): void {
    this.stopAndClear();
    this.queue = [];
    this.play(blob);
  }

  /**
   * Method to stop current audio from playing and empties queue
   */
  stopAndClear(): void {
    this.queue = [];
    this.audioElement.pause();
    this.$playing.next(false);
  }
}
