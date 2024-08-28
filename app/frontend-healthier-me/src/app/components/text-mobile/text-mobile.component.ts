import { Component, Input } from "@angular/core";
import { MessageRole } from "../../types/message.type";
import { BehaviorSubject, takeWhile } from "rxjs";
import { Profile } from "../../types/profile.type";
import { Message } from "../../types/message.type";
import { FollowUp } from "../../types/follow-up.type";
import { ChatMessageService } from "../../services/chat-message/chat-message.service";
import { ChatFollowupService } from "../../services/chat-followup/chat-followup.service";
import { ProfileService } from "../../services/profile/profile.service";
import { ActivatedRoute } from "@angular/router";
import { TextUserComponent } from "../text/text-user/text-user.component";
import { TextSystemComponent } from "../text/text-system/text-system.component";
import { TextFollowupComponent } from "../text/text-followup/text-followup.component";
import { TextInputComponent } from "../text/text-input/text-input.component";
import { StickyBottomDirective } from "../../directives/stick-bottom/sticky-bottom.directive";

@Component({
  selector: "app-text-mobile",
  standalone: true,
  imports: [TextUserComponent, TextSystemComponent, TextFollowupComponent, TextInputComponent, StickyBottomDirective],
  templateUrl: "./text-mobile.component.html",
  styleUrl: "./text-mobile.component.css"
})
export class TextMobileComponent implements OnInit {
  @Input() showTextInput?: boolean = true;

  user: string = MessageRole.User;
  system: string = MessageRole.Assistant;
  profile: BehaviorSubject<Profile | undefined> = new BehaviorSubject<Profile | undefined>(undefined);

  messages: Message[] = [];
  followUps: FollowUp[] = [];

  constructor(
    private chatMessageService: ChatMessageService,
    private followUpService: ChatFollowupService,
    private profileService: ProfileService,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    this.route.paramMap
      .pipe(
        takeWhile(p => {
          return p.get("profileId") !== undefined;
        }, true)
      )
      .subscribe(p => {
        this.profile = this.profileService.getProfile(p.get("profileId")!);
      });

    this.profile.subscribe(p => {
      if (!p) {
        return;
      }
      this.chatMessageService.load(p.id).then(m => {
        m.subscribe(messages => {
          this.messages = messages;

          if (this.messages.length === 0) {
            this.upsertIntroMessage(p.id);
          }
        });
      });
    });
  }

  private async upsertIntroMessage(profileId: string): Promise<void> {
    const introMessage: Message = {
      id: "intro-message", // Assign a unique ID for the intro message
      profile_id: profileId,
      role: MessageRole.Assistant,
      message: "Welcome! How can I assist you today?",
      timestamp: Date.now(),
      sources: []
    };

    await this.chatMessageService.upsert(introMessage);

    // After upserting, refresh the message list to ensure it's reflected
    this.messages = await this.chatMessageService.staticLoad(profileId);
  }
}
