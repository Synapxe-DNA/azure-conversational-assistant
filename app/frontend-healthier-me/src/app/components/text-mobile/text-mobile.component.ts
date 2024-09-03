import { Component, Input, OnInit } from "@angular/core";
import { MessageRole } from "../../types/message.type";
import { BehaviorSubject, takeWhile } from "rxjs";
import { Profile } from "../../types/profile.type";
import { Message } from "../../types/message.type";
import { ChatMessageService } from "../../services/chat-message/chat-message.service";
import { ProfileService } from "../../services/profile/profile.service";
import { ActivatedRoute } from "@angular/router";
import { TextUserComponent } from "../text/text-user/text-user.component";
import { TextSystemComponent } from "../text/text-system/text-system.component";
import { TextInputComponent } from "../text/text-input/text-input.component";
import { StickyBottomDirective } from "../../directives/stick-bottom/sticky-bottom.directive";

@Component({
  selector: "app-text-mobile",
  standalone: true,
  imports: [TextUserComponent, TextSystemComponent, TextInputComponent, StickyBottomDirective],
  templateUrl: "./text-mobile.component.html",
  styleUrl: "./text-mobile.component.css"
})
export class TextMobileComponent implements OnInit {
  @Input() showTextInput?: boolean = true;

  user: string = MessageRole.User;
  system: string = MessageRole.Assistant;
  profile: BehaviorSubject<Profile | undefined> = new BehaviorSubject<Profile | undefined>(undefined);

  messages: Message[] = [];

  constructor(
    private chatMessageService: ChatMessageService,
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
        });
      });
    });
  }
}
