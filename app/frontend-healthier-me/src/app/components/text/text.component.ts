import { Component, ElementRef, OnInit, ViewChild } from "@angular/core";
import { CommonModule } from "@angular/common";
import { FormsModule } from "@angular/forms";
import { LucideAngularModule } from "lucide-angular";
import { Message, MessageRole, MessageSource } from "../../types/message.type";
import { TextInputComponent } from "../text/text-input/text-input.component";
import { TextSystemComponent } from "../text/text-system/text-system.component";
import { TextUserComponent } from "./text-user/text-user.component";
import { ChatMessageService } from "../../services/chat-message/chat-message.service";
import {BehaviorSubject, filter, take} from "rxjs";
import { Profile } from "../../types/profile.type";
import { ProfileService } from "../../services/profile/profile.service";
import { ActivatedRoute } from "@angular/router";

const sources: MessageSource[] = [
  {
    title: "When is Your Baby Due?",
    description: "When is Your Baby Due?",
    url: "https://www.healthhub.sg/live-healthy/when-is-your-baby-due",
    cover_image_url: "https://ch-api.healthhub.sg/api/public/content/8692c864101e4603868fb170c00230fe?v=534ae16e&t=livehealthyheaderimage",
  },
  {
    title: "Important Nutrients: What Should You Eat More Of?",
    description: "Important Nutrients: What Should You Eat More Of? Important Nutrients: What Should You Eat More Of? Important Nutrients: What Should You Eat More Of?",
    url: "https://www.healthhub.sg/live-healthy/important-nutrients-what-should-you-eat-more-of",
    cover_image_url: "https://ch-api.healthhub.sg/api/public/content/3885d0458c0a4521beb14ca352730423?v=646204cc&t=livehealthyheaderimage",
  }
];


@Component({
  selector: "app-text",
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule, TextInputComponent, TextSystemComponent, TextUserComponent],
  templateUrl: "./text.component.html",
  styleUrls: ["./text.component.css"],
})

export class TextComponent implements OnInit{
  user: string = MessageRole.User
  system: string = MessageRole.System
  profile:BehaviorSubject<Profile|undefined> = new BehaviorSubject<Profile|undefined>(undefined)
  messages: Message[] = []

  constructor(
    private chatMessageService: ChatMessageService,
    private profileService: ProfileService,
    private route: ActivatedRoute
  ) {
  }

  ngOnInit(): void {
    this.profile = this.profileService.getProfile(this.route.snapshot.paramMap.get('profileId') as string)

    this.profile
      .subscribe((p)  => {
        this.chatMessageService.load(p?.id || "general")
          .then(m => {
            m.subscribe(messages => this.messages=messages)
          })
    })
  }
}
