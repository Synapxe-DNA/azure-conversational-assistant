import { Component, ElementRef, Input, OnInit, ViewChild } from "@angular/core";
import { CommonModule } from "@angular/common";
import { FormsModule } from "@angular/forms";
import { LucideAngularModule } from "lucide-angular";
import { Message, MessageRole, MessageSource } from "../../types/message.type";
import { TextInputComponent } from "../text/text-input/text-input.component";
import { TextSystemComponent } from "../text/text-system/text-system.component";
import { TextUserComponent } from "./text-user/text-user.component";
import { ChatMessageService } from "../../services/chat-message/chat-message.service";
import { BehaviorSubject, filter, take, takeWhile } from "rxjs";
import { GeneralProfile, Profile } from "../../types/profile.type";
import { ProfileService } from "../../services/profile/profile.service";
import { ActivatedRoute } from "@angular/router";
import { createId } from "@paralleldrive/cuid2";
import { TextClipboardComponent } from "./text-clipboard/text-clipboard.component";
import { StickyBottomDirective } from "../../directives/stick-bottom/sticky-bottom.directive";
import { TextFollowupComponent } from "./text-followup/text-followup.component";
import { FollowUp } from "../../types/follow-up.type";
import { ChatFollowupService } from "../../services/chat-followup/chat-followup.service";

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
    TextFollowupComponent,
    StickyBottomDirective,
  ],
  templateUrl: "./text.component.html",
  styleUrls: ["./text.component.css"],
})
export class TextComponent implements OnInit {
  @Input() showTextInput?: boolean = true;

  user: string = MessageRole.User;
  system: string = MessageRole.Assistant;
  profile: BehaviorSubject<Profile | undefined> = new BehaviorSubject<
    Profile | undefined
  >(undefined);

  messages: Message[] = [];
  followUps: FollowUp[] = []

  constructor(
    private chatMessageService: ChatMessageService,
    private followUpService: ChatFollowupService,
    private profileService: ProfileService,
    private route: ActivatedRoute,
  ) {}

  ngOnInit(): void {
    this.route.paramMap
      .pipe(
        takeWhile((p) => {
          return p.get("profileId") !== undefined;
        }, true),
      )
      .subscribe((p) => {
        this.profile = this.profileService.getProfile(p.get("profileId")!);
      });

    this.profile.subscribe((p) => {
      if (!p) {
        return;
      }
      this.chatMessageService.load(p.id).then((m) => {
        m.subscribe((messages) => {
          this.messages = messages;
        });
      });
    });

    this.route.paramMap
      .pipe(
        takeWhile((p) => {
          return p.get("profileId") !== undefined;
        }, true),
      )
      .subscribe((p) => {
        this.profile = this.profileService.getProfile(p.get("profileId")!);
      });

    this.profile.subscribe((p) => {
      if (!p) {
        return;
      }
      this.followUpService.load(p.id).then((m) => {
        m.subscribe((followUps) => {
          this.followUps = followUps;
        });
      });
    });
  }
}
 