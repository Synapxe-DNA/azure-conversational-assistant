export class AudioAnalyser {
  private readonly numBars: number
  private readonly analyser: AnalyserNode

  /**
   * Constructs an instance of AudioAnalyser.
   * @param stream The media stream to analyse.
   * @param numBars The number of frequency bars to return.
   * @param smoothing Smoothing Time Constant
   */
  constructor(stream: MediaStream, numBars: number=8, smoothing:number=0.75) {
    this.numBars = numBars

    // Initialize audio context and analyser
    const audioContext = new AudioContext()
    this.analyser = audioContext.createAnalyser()
    this.analyser.fftSize = 64
    this.analyser.minDecibels = -110
    this.analyser.maxDecibels = -45
    this.analyser.smoothingTimeConstant = smoothing

    // Connect the media stream source to the analyser
    const source = audioContext.createMediaStreamSource(stream)
    source.connect(this.analyser)
  }

  /**
   * Retrieves normalized frequency data as an array of values scaled between 0 and 1.
   * @returns An array of frequency values.
   */
  getFrequency(): number[] {
    const bufferLength = this.analyser.frequencyBinCount
    const dataArray = new Uint8Array(bufferLength)
    this.analyser.getByteFrequencyData(dataArray)

    // Normalize and sample the dataArray to match the number of bars
    const step = Math.floor(bufferLength / this.numBars)
    const frequencyData = new Array(this.numBars).fill(0)

    for (let i = 0; i < this.numBars; i++) {
      let sum = 0
      // Sum up values over 'step' to reduce the array size and average it
      for (let j = 0; j < step; j++) {
        sum += dataArray[i * step + j]
      }
      // Normalize the averaged value to be between 0 and 1
      frequencyData[i] = sum / (step * 255)
    }

    return frequencyData
  }

  /**
   * Retrieves the overall audio level as a single value between 0 and 1.
   * @returns The average audio level.
   */
  getAudioLevel(): number {
    const frequencyData = this.getFrequency();
    const sum = frequencyData.reduce((acc, value) => acc + value, 0);
    return sum / frequencyData.length;
  }
}
