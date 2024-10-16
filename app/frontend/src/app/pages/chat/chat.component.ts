import { Component, HostListener, OnDestroy } from "@angular/core";
import { ChatMode } from "../../types/chat-mode.type";
import { PreferenceService } from "../../services/preference/preference.service";
import { VoiceComponent } from "../../components/voice/voice.component";
import { TextComponent } from "../../components/text/text.component";
import { VoiceMobileComponent } from "../../components/voice-mobile/voice-mobile.component";
import { TextMobileComponent } from "../../components/text-mobile/text-mobile.component";
import { ConvoBrokerService } from "../../services/convo-broker/convo-broker.service";
import { HttpClient } from "@angular/common/http";

@Component({
  selector: "app-chat",
  standalone: true,
  imports: [VoiceComponent, TextComponent, VoiceMobileComponent, TextMobileComponent],
  templateUrl: "./chat.component.html",
  styleUrl: "./chat.component.css"
})
export class ChatComponent {
  chatMode?: ChatMode;

  constructor(
    private preference: PreferenceService,
    private convoBroker: ConvoBrokerService
  ) {
    this.preference.$chatMode.subscribe(m => {
      this.chatMode = m;
    });
    this.convoBroker.openWebSocket();
  }
  protected readonly ChatMode = ChatMode;
}
