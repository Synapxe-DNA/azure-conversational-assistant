import { createId } from "@paralleldrive/cuid2";
import { BehaviorSubject } from "rxjs";
import { GeneralProfile, Profile } from "../../types/profile.type";
import { ProfileService } from "../../services/profile/profile.service";
import { ChatMessageService } from "../../services/chat-message/chat-message.service";
import { MessageRole } from "../../types/message.type";

export class v2AudioRecorder {
  socket?: WebSocket;
  audioContext?: AudioContext;
  processor?: ScriptProcessorNode;
  pcmData?: Int16Array;
  pcmDataList?: Int16Array[];

  userMessageId: string = "";
  private activeProfile: BehaviorSubject<Profile | undefined> = new BehaviorSubject<Profile | undefined>(undefined);
  finalText: string = "";
  isFinal: boolean = false;
  requestTime: number = 0;

  constructor(
    private chatMessageService: ChatMessageService,
    private profileService: ProfileService
  ) {
    this.profileService.$currentProfileInUrl.subscribe(p => {
      this.activeProfile = this.profileService.getProfile(p);
    });
  }

  setupWebSocket() {
    this.socket = new WebSocket("/ws/transcribe");
    this.socket.onopen = () => {
      console.log("WebSocket connection opened");
      this.resetFields();
    };

    this.socket.onerror = error => {
      console.error("WebSocket error:", error);
    };

    this.socket.onclose = () => {
      console.log("WebSocket connection closed");
      this.socket = undefined;
    };

    this.socket.onmessage = event => {
      try {
        const data = JSON.parse(event.data);
        if (data.text) {
          this.finalText = data.text;
          this.upsert(this.finalText);
          this.isFinal = data.is_final;
        } else if (data.error) {
          console.error("Error:", data.error);
        }
      } catch (error) {
        console.error("Error parsing message:", error);
      }
    };
  }

  closeWebSocket() {
    this.socket?.close();
    this.socket = undefined;
  }

  startAudioCapture() {
    if (this.socket === undefined) {
      this.setupWebSocket();
    }
    this.resetFields();
    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then(stream => {
        this.audioContext = new AudioContext();
        this.pcmDataList = [];
        const source = this.audioContext.createMediaStreamSource(stream);
        this.processor = this.audioContext.createScriptProcessor(1024, 1, 1);

        source.connect(this.processor);
        this.processor.connect(this.audioContext.destination);
        const sampleRate = 16000;
        const downsampleFactor = this.audioContext.sampleRate / sampleRate;

        let sampleCounter = 0;

        this.processor.onaudioprocess = e => {
          const inputBuffer = e.inputBuffer.getChannelData(0);
          const outputBuffer = new Float32Array(Math.floor(inputBuffer.length / downsampleFactor));

          for (let i = 0; i < outputBuffer.length; i++) {
            sampleCounter += downsampleFactor;
            outputBuffer[i] = inputBuffer[Math.floor(sampleCounter) - 1];
          }

          sampleCounter = sampleCounter % 1;

          /// convert to 16-bit PCM
          this.pcmData = new Int16Array(outputBuffer.length);
          for (let i = 0; i < outputBuffer.length; i++) {
            this.pcmData[i] = Math.max(-1, Math.min(1, outputBuffer[i])) * 0x7fff;
          }

          // Send pcmData to backend
          if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.sendAllPcmData();
          } else {
            this.pcmDataList!.push(this.pcmData);
          }
          this.pcmData = new Int16Array(0); // Clear the buffer
        };
      })
      .catch(error => {
        console.error("Error accessing microphone:", error);
      });
  }

  stopAudioCapture(): Promise<string> {
    return new Promise(resolve => {
      if (this.processor) {
        this.processor.disconnect();
        this.processor = undefined;
      }
      if (this.audioContext) {
        this.audioContext.close();
        this.audioContext = undefined;
      }

      const checkBufferInterval = setInterval(() => {
        console.log("Clearing all PCM buffer");
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
          this.sendAllPcmData();
          clearInterval(checkBufferInterval); // Stop checking once the buffer is empty
          this.socket?.send("completed"); // Send completed message to backend
        }
      }, 100);

      const checkInterval = setInterval(() => {
        if (this.isFinal) {
          clearInterval(checkInterval); // Stop checking once the socket is closed
          this.upsert(this.finalText); // Final upsert to ensure final text is displayed
          console.log("Speech transcribed successfully");
          resolve(this.finalText);
        }
      }, 100);
    });
  }

  resetFields() {
    this.userMessageId = createId();
    this.finalText = "";
    this.isFinal = false;
    this.requestTime = new Date().getTime();
  }

  sendAllPcmData() {
    while (this.pcmDataList!.length > 0) {
      const data = this.pcmDataList!.shift(); // Pop the first item
      if (data) {
        this.socket!.send(data.buffer);
      }
    }
    if (this.pcmData!.length > 0) {
      this.socket!.send(this.pcmData!.buffer);
    }
  }

  async upsert(finalText: string) {
    await this.chatMessageService.upsert({
      id: this.userMessageId,
      profile_id: this.activeProfile.getValue()?.id || GeneralProfile.id,
      role: MessageRole.User,
      message: finalText,
      timestamp: this.requestTime,
      sources: []
    });
  }
}
