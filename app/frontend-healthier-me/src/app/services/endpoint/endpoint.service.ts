import { Injectable } from "@angular/core";
import { Profile } from "../../types/profile.type";
import { BehaviorSubject } from "rxjs";
import { VoiceResponse } from "../../types/responses/voice-response.type";
import { Message } from "../../types/message.type";
import { ChatResponse } from "../../types/responses/chat-response.type";

@Injectable({
  providedIn: "root",
})
export class EndpointService {
  constructor() {}

  async sendVoice(
    audio: Blob,
    profile: Profile,
    history: Message[],
  ): Promise<BehaviorSubject<VoiceResponse>> {
    return undefined as unknown as BehaviorSubject<VoiceResponse>;
  }

  async sendChat(
    message: Message,
    profile: Profile,
    history: Message[],
  ): Promise<BehaviorSubject<ChatResponse>> {
    return undefined as unknown as BehaviorSubject<ChatResponse>;
  }
}
