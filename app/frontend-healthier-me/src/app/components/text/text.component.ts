import { Component, ElementRef, OnInit, ViewChild } from "@angular/core";
import { CommonModule } from "@angular/common";
import { FormsModule } from "@angular/forms";
import { LucideAngularModule } from "lucide-angular";
import { Message, MessageRole, MessageSource } from "../../types/message.type";
import { TextInputComponent } from "../text/text-input/text-input.component";
import { TextSystemComponent } from "../text/text-system/text-system.component";
import { TextUserComponent } from "./text-user/text-user.component";
import { ChatMessageService } from "../../services/chat-message/chat-message.service";
import { BehaviorSubject, filter, take } from "rxjs";
import { Profile } from "../../types/profile.type";
import { ProfileService } from "../../services/profile/profile.service";
import { ActivatedRoute } from "@angular/router";


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
  ],
  templateUrl: "./text.component.html",
  styleUrls: ["./text.component.css"],
})
export class TextComponent implements OnInit {
  user: string = MessageRole.User;
  system: string = MessageRole.System;
  profile: BehaviorSubject<Profile | undefined> = new BehaviorSubject<
    Profile | undefined
  >(undefined);
  messages: Message[] = [];

  constructor(
    private chatMessageService: ChatMessageService,
    private profileService: ProfileService,
    private route: ActivatedRoute,
  ) {}

  ngOnInit(): void {
    this.profile = this.profileService.getProfile(
      this.route.snapshot.paramMap.get("profileId") as string,
    );

    this.profile.subscribe((p) => {
      this.chatMessageService.load(p?.id || "general").then((m) => {
        m.subscribe((messages) => (this.messages = messages));
      });
    });
  }
}
