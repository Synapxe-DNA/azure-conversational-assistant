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

  private silentAudioBlob: Blob = this.createSilentAudioBlob();

  $stream: BehaviorSubject<MediaStream | null> = new BehaviorSubject<MediaStream | null>(null);
  $playing: BehaviorSubject<boolean> = new BehaviorSubject<boolean>(false);
  playingSilent: boolean = false;

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
    this.playingSilent = false;
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

  /**
   * Method to play silent audio
   */
  playSilentAudio(): void {
    this.playingSilent = true;
    const blob = [this.silentAudioBlob];
    blob.forEach(b => this.queue.push(b));
    if (!this.$playing.value) {
      this.playNextInQueue();
    }
  }

  /**
   * Method to create a silent audio blob
   */

  private createSilentAudioBlob(duration = 0.01, sampleRate = 44100, channels = 1) {
    const numSamples = Math.floor(sampleRate * duration);
    const buffer = new ArrayBuffer(44 + numSamples * channels * 2); // 44 bytes for WAV header + data
    const view = new DataView(buffer);

    // WAV header
    // ChunkID 'RIFF'
    view.setUint32(0, 0x52494646, false);
    // ChunkSize
    view.setUint32(4, 36 + numSamples * channels * 2, true);
    // Format 'WAVE'
    view.setUint32(8, 0x57415645, false);
    // Subchunk1ID 'fmt '
    view.setUint32(12, 0x666d7420, false);
    // Subchunk1Size (16 for PCM)
    view.setUint32(16, 16, true);
    // AudioFormat (1 for PCM)
    view.setUint16(20, 1, true);
    // NumChannels
    view.setUint16(22, channels, true);
    // SampleRate
    view.setUint32(24, sampleRate, true);
    // ByteRate (SampleRate * NumChannels * BitsPerSample / 8)
    view.setUint32(28, sampleRate * channels * 2, true);
    // BlockAlign (NumChannels * BitsPerSample / 8)
    view.setUint16(32, channels * 2, true);
    // BitsPerSample
    view.setUint16(34, 16, true);
    // Subchunk2ID 'data'
    view.setUint32(36, 0x64617461, false);
    // Subchunk2Size (NumSamples * NumChannels * BitsPerSample / 8)
    view.setUint32(40, numSamples * channels * 2, true);

    // PCM data (silence = 0 amplitude)
    let offset = 44;
    for (let i = 0; i < numSamples; i++) {
      view.setInt16(offset, 0, true); // 16-bit PCM, 0 amplitude for silence
      offset += 2;
    }

    // Create Blob
    const blob = new Blob([view], { type: "audio/wav" });
    return blob;
  }
}
