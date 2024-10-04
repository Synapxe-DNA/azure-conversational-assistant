import { Injectable } from "@angular/core";

@Injectable({
  providedIn: "root"
})
export class AudioService {
  constructor() {}

  /**
   * Method to get the media stream of the default mic input
   * @return {Promise<MediaStream>}
   */
  async getMicInput(): Promise<MediaStream> {
    return navigator.mediaDevices.getUserMedia({ audio: true });
    // return new MediaStream();
  }

/**
 * Method to remove all tracks from a given media stream
 * @param {MediaStream} stream - The MediaStream from which tracks are to be removed
 */
async stopTracks(stream: MediaStream) {
  if (stream) {
    // Loop through all the tracks and stop each one
    stream.getTracks().forEach(track => {
      track.stop();  // Stops the track and releases the resource
      stream.removeTrack(track);  // Removes the track from the stream
    });
  }
}


  /**
   * Method to combine audio streams into a single stream
   * @param streams {MediaStream[]}
   * @return {Promise<MediaStream>}
   */
  async mergeAudioStreams(...streams: MediaStream[]): Promise<MediaStream> {
    const audioContext = new AudioContext();
    const audioDestination = audioContext.createMediaStreamDestination();

    streams.forEach(s => {
      audioDestination.connect(audioContext.createMediaStreamSource(s));
    });

    return audioDestination.stream;
  }
}
