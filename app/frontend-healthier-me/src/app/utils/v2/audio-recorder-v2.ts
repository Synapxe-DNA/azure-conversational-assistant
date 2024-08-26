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

  userMessageId: string = "";
  private activeProfile: BehaviorSubject<Profile | undefined> =
    new BehaviorSubject<Profile | undefined>(undefined);
  finalText: string = "";
  requestTime: number = 0;

  constructor(
    private chatMessageService: ChatMessageService,
    private profileService: ProfileService,
  ) {
    this.profileService.$currentProfileInUrl.subscribe((p) => {
      this.activeProfile = this.profileService.getProfile(p);
    });
  }

  setupWebSocket() {
    this.socket = new WebSocket("/ws/transcribe");

    this.socket.onopen = () => {
      console.log("WebSocket connection opened");
      this.resetFields();
      this.startAudioCapture();
    };

    this.socket.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    this.socket.onclose = () => {
      console.log("WebSocket connection closed");
      this.stopAudioCapture();
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.text) {
          
          this.finalText += data.text
          // upsert user message
          console.log("onMessage final text", this.finalText)
          this.upsert(this.finalText);
        } else if (data.error) {
          console.error("Error:", data.error);
        }
      } catch (error) {
        console.error("Error parsing message:", error);
      }
    };
  }

  startAudioCapture() {
    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then((stream) => {
        this.audioContext = new AudioContext();
        const source = this.audioContext.createMediaStreamSource(stream);
        this.processor = this.audioContext.createScriptProcessor(1024, 1, 1);

        source.connect(this.processor);
        this.processor.connect(this.audioContext.destination);
        const sampleRate = 16000;
        const downsampleFactor = this.audioContext.sampleRate / sampleRate;

        let sampleCounter = 0;

        this.processor.onaudioprocess = (e) => {
          const inputBuffer = e.inputBuffer.getChannelData(0);
          const outputBuffer = new Float32Array(
            Math.floor(inputBuffer.length / downsampleFactor),
          );

          for (let i = 0; i < outputBuffer.length; i++) {
            sampleCounter += downsampleFactor;
            outputBuffer[i] = inputBuffer[Math.floor(sampleCounter) - 1];
          }

          sampleCounter = sampleCounter % 1;

          /// convert to 16-bit PCM
          const pcmData = new Int16Array(outputBuffer.length);
          for (let i = 0; i < outputBuffer.length; i++) {
            pcmData[i] = Math.max(-1, Math.min(1, outputBuffer[i])) * 0x7fff;
          }

          // Send pcmData to backend
          if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(pcmData.buffer);
          }
        };
      })
      .catch((error) => {
        console.error("Error accessing microphone:", error);
      });
  }

  stopAudioCapture(): Promise<string> {
    return new Promise((resolve) => {
      if (this.processor) {
        this.processor.disconnect();
        this.processor = undefined;
      }
      if (this.audioContext) {
        this.audioContext.close();
        this.audioContext = undefined;
      }
      resolve(this.finalText);
    });
  }

  resetFields() {
    this.userMessageId = createId();
    console.log("reset fields userid",this.userMessageId)
    this.finalText = "";
    this.requestTime = new Date().getTime();
  }

  getUserId (): string {
    return this.userMessageId
  }

  async upsert(finalText: string) {
    console.log("upsert userid",this.getUserId())
    await this.chatMessageService.upsert({
      id: this.getUserId(),
      profile_id: this.activeProfile.getValue()?.id || GeneralProfile.id,
      role: MessageRole.User,
      message: finalText,
      timestamp: this.requestTime,
      sources: [],
    });
  }
}
