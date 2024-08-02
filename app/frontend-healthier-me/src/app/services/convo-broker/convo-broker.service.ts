import { Injectable } from "@angular/core";
import { ChatMessageService } from "../chat-message/chat-message.service";
import { AudioPlayerService } from "../audio-player/audio-player.service";
import { EndpointService } from "../endpoint/endpoint.service";
import { Profile } from "../../types/profile.type";
import { Message, MessageRole } from "../../types/message.type";
import { createId } from "@paralleldrive/cuid2";

@Injectable({
  providedIn: "root",
})
export class ConvoBrokerService {
  constructor(
    private chatMessageService: ChatMessageService,
    private audioPlayer: AudioPlayerService,
    private endpointService: EndpointService,
  ) {}

  async sendVoice(audio: Blob, profile: Profile) {
    const history: Message[] = await this.chatMessageService.staticLoad(
      profile.id,
    );
    await this.endpointService.sendVoice(audio, profile, history);
  }

  async sendChat(message: string, profile: Profile) {
    const newMessage: Message = {
      id: createId(),
      message: message,
      profile_id: profile.id,
      role: MessageRole.User,
      timestamp: new Date().getTime(),
    };

    const history: Message[] = await this.chatMessageService.staticLoad(
      profile.id,
    );
    await this.endpointService.sendChat(newMessage, profile, history);
  }
}
