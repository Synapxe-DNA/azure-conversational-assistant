import { Component } from "@angular/core";
import { ChatMode } from "../../types/chat-mode.type";
import { PreferenceService } from "../../services/preference/preference.service";
import { VoiceComponent } from "../../components/voice/voice.component";
import { TextComponent } from "../../components/text/text.component";
import { Router } from "@angular/router";

@Component({
  selector: "app-chat",
  standalone: true,
  imports: [VoiceComponent, TextComponent],
  templateUrl: "./chat.component.html",
  styleUrl: "./chat.component.css",
})
export class ChatComponent {
  chatMode?: ChatMode;

  constructor(private preference: PreferenceService) {
    this.preference.$chatMode.subscribe((m) => {
      this.chatMode = m;
    });
  }

  protected readonly ChatMode = ChatMode;
}
