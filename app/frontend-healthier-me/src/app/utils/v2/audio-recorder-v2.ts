export class v2AudioRecorder {
    socket?: WebSocket;
    audioContext?: AudioContext;
    processor?: ScriptProcessorNode;

    setupWebSocket() {
        this.socket = new WebSocket('${protocol}//${window.location.hostname}:8000/ws/transcribe');

        this.socket.onopen = () => {
            console.log('WebSocket connection opened');

        };
        this.socket.onmessage = (event) => {
            console.log('Received message from server:', event.data);
        };
        this.socket.onclose = () => {
            console.log('WebSocket connection closed');
        };
    }

    startAudioCapture() {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                this.audioContext = new AudioContext();
                const source = this.audioContext.createMediaStreamSource(stream);
                this.processor = this.audioContext.createScriptProcessor(1024, 1, 1);

                source.connect(this.processor)
                this.processor.connect(this.audioContext.destination);
                const sampleRate = 16000
                const downsampleFactor = this.audioContext.sampleRate / sampleRate;

                let sampleCounter = 0;

                this.processor.onaudioprocess = (e) => {
                    const inputBuffer = e.inputBuffer.getChannelData(0)
                    const outputBuffer = new Float32Array(Math.floor(inputBuffer.length / downsampleFactor))

                    for (let i = 0; i < outputBuffer.length; i++) {
                        sampleCounter += downsampleFactor
                        outputBuffer[i] = inputBuffer[Math.floor(sampleCounter) - 1];
                    }

                    sampleCounter = sampleCounter % 1

                    /// convert to 16-bit PCM
                    const pcmData = new Int16Array(outputBuffer.length)
                    for (let i = 0; i < outputBuffer.length; i++) {
                        pcmData[i] = Math.max(-1, Math.min(1, outputBuffer[i])) * 0x7FFF;
                    }

                    // Send pcmData to backend
                    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                        this.socket.send(pcmData.buffer);
                    }
                }
            }

            )
    }
}
