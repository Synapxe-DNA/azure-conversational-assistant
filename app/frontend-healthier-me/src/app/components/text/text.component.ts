import { Component, Input, OnInit } from "@angular/core";
import { CommonModule } from "@angular/common";
import { FormsModule } from "@angular/forms";
import { LucideAngularModule } from "lucide-angular";
import { Message, MessageRole } from "../../types/message.type";
import { TextInputComponent } from "../text/text-input/text-input.component";
import { TextSystemComponent } from "../text/text-system/text-system.component";
import { TextUserComponent } from "./text-user/text-user.component";
import { ChatMessageService } from "../../services/chat-message/chat-message.service";
import { BehaviorSubject, takeWhile } from "rxjs";
import { Profile } from "../../types/profile.type";
import { ProfileService } from "../../services/profile/profile.service";
import { ActivatedRoute } from "@angular/router";
import { TextClipboardComponent } from "./text-clipboard/text-clipboard.component";
import { StickyBottomDirective } from "../../directives/stick-bottom/sticky-bottom.directive";

@Component({
  selector: "app-text",
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    LucideAngularModule,
    TextInputComponent,
    TextSystemComponent,
    TextUserComponent,
    TextClipboardComponent,
    StickyBottomDirective
  ],
  templateUrl: "./text.component.html",
  styleUrls: ["./text.component.css"]
})
export class TextComponent implements OnInit {
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
