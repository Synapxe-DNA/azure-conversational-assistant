import { Component, HostListener } from "@angular/core";
import { ChatMode } from "../../types/chat-mode.type";
import { PreferenceService } from "../../services/preference/preference.service";
import { VoiceComponent } from "../../components/voice/voice.component";
import { TextComponent } from "../../components/text/text.component";
import { VoiceMobileComponent } from "../../components/voice-mobile/voice-mobile.component";
import { TextMobileComponent } from "../../components/text-mobile/text-mobile.component";

@Component({
  selector: "app-chat",
  standalone: true,
  imports: [VoiceComponent, TextComponent, VoiceMobileComponent, TextMobileComponent],
  templateUrl: "./chat.component.html",
  styleUrl: "./chat.component.css"
})
export class ChatComponent {
  chatMode?: ChatMode;
  isMobile?: boolean;

  constructor(private preference: PreferenceService) {
    this.preference.$chatMode.subscribe(m => {
      this.chatMode = m;
    });
    this.isMobile = window.innerWidth < 768;
  }

  @HostListener("window:resize", ["$event"])
  onResize(event: any) {
    this.checkViewport();
  }
  checkViewport() {
    this.isMobile = window.innerWidth < 768; // Adjust this value as needed
  }

  protected readonly ChatMode = ChatMode;
}
