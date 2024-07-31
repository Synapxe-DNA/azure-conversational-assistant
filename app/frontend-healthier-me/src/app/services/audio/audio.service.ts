import { Injectable } from "@angular/core"

@Injectable({
  providedIn: "root",
})
export class AudioService {
  constructor() {}

  async getMicInput(): Promise<MediaStream> {
    return navigator.mediaDevices.getUserMedia({ audio: true })
  }

  /**
   * Method to combine audio streams into a single stream
   * @param streams {MediaStream[]}
   * @return {Promise<MediaStream>}
   */
  async mergeAudioStreams(...streams: MediaStream[]): Promise<MediaStream> {
    const audioContext = new AudioContext()
    const audioDestination = audioContext.createMediaStreamDestination()

    streams.forEach((s) => {
      audioDestination.connect(audioContext.createMediaStreamSource(s))
    })

    return audioDestination.stream
  }
}
