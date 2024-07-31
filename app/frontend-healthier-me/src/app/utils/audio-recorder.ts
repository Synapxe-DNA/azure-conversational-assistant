import {first, Subject, take} from "rxjs";

/**
 * Class to handle audio recordings and processing
 */
export class AudioRecorder {

  private readonly stream: MediaStream
  private readonly slice: number

  private readonly mimeType: string = ""
  private readonly fileExtension: string = ""

  private recorder: MediaRecorder | undefined

  private chunks: BlobPart[] = []
  private trailingChunk: BlobPart | undefined


  private flagStartRecording: boolean = false
  private flagChunkRecorded: Subject<void> = new Subject<void>()

  /**
   * @constructor
   * @param stream {MediaStream} containing the target audio
   * @param slice {number} Time of each audio slice (in ms)
   */
  constructor(
    stream: MediaStream,
    slice: number = 5000
  ) {
    this.stream = stream
    this.slice = slice

    // Determine the supported MIME type and set it
    const options: { mimeType: string, extension: string }[] = [
      { mimeType: 'audio/webm', extension: 'webm' },
      { mimeType: 'audio/mp4', extension: 'm4a' }  // typically used by Safari
    ]

    // Iterate over all available options until a suitable option is found
    for (const option of options) {
      if (MediaRecorder.isTypeSupported(option.mimeType)) {
        this.mimeType = option.mimeType
        this.fileExtension = option.extension
        break
      }
    }

    if (!this.mimeType || !this.fileExtension) {
      throw new Error("Unable to set recording option. MimeType not supported!")
    }

    this.initializeRecorder()
  }

  /**
   * Method to initialize the MediaRecorder
   */
  initializeRecorder() {
    this.chunks = []
    this.trailingChunk = undefined
    this.flagStartRecording = false
    this.recorder = new MediaRecorder(this.stream, { mimeType: this.mimeType })
    this.recorder.ondataavailable = (e) => { this.handleChunk(e) }
    this.recorder.onerror = console.error

    /**
     * The recorder is paused instead of starting in the start() method as the original intention was to record the
     * slice right before recorder.start() was called, since the voice activation will take a while. However, this led
     * to problems with the blob as all slices of the blob need to be in sequence, and this was an intended feature.
     *
     * - See: https://bugzilla.mozilla.org/show_bug.cgi?id=898771
     *
     * As such, the code was written in a way that if this door is opened again in the future, or if our backend can do
     * real time TTS (so we can move away from the browser based VAD), then we can possibly stream the chunks to the
     * backend.
     */
    this.recorder.start(this.slice)
    this.recorder.pause()
  }

  /**
   * Method to append chunk to chunks
   * @param e {BlobEvent}
   * @private
   */
  private handleChunk(e: BlobEvent) {
    this.chunks.push(e.data)
    this.flagChunkRecorded.next()
  }

  /**
   * Method to start recording
   */
  start(): void {
    if (!this.recorder) {
      throw new Error('MediaRecorder is not initialized')
    }

    this.recorder.resume()

    // Resets local states
    this.flagStartRecording = true

  }

  /**
   * Method to stop recording, and get the resulting file
   * @return {Promise<{data: Blob, extension: string}>}
   */
  stop(): Promise<{ data: Blob, extension: string }> {

    console.log("Stopping!")

    if (!this.recorder) {
      throw new Error("MediaRecorder was not initialised!")
    }

    // Reset the recorder to prepare for the next recording session

    this.recorder!.requestData()
    return new Promise<{ data: Blob, extension: string }>((resolve) => {
      // Handle stop event triggered by AudioRecorder.handleChunk
      this.flagChunkRecorded.pipe(first()).subscribe(() => {
        const finalBlob = new Blob(this.chunks, { type: this.mimeType })
        resolve({
          data: finalBlob,
          extension: this.fileExtension
        })
        this.initializeRecorder()
      })
      this.recorder!.stop()
    })

  }
}
