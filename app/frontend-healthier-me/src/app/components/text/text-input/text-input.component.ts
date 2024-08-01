import { Component, OnInit } from "@angular/core";
import { MessageRole, MessageSource } from "../../../types/message.type";
import { LucideAngularModule } from "lucide-angular";
import {
  FormControl,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
} from "@angular/forms";
import { CommonModule } from "@angular/common";
import { InputTextModule } from "primeng/inputtext";
import { ChatMessageService } from "../../../services/chat-message/chat-message.service";
import { createId } from "@paralleldrive/cuid2";
import { ProfileService } from "../../../services/profile/profile.service";
import { BehaviorSubject } from "rxjs";
import { Profile } from "../../../types/profile.type";
import { ActivatedRoute } from "@angular/router";
import { Button } from "primeng/button";
import { PreferenceService } from "../../../services/preference/preference.service";
import { ChatMode } from "../../../types/chat-mode.type";

const sources: MessageSource[] = [
  {
    title: "When is Your Baby Due?",
    description: "When is Your Baby Due?",
    url: "https://www.healthhub.sg/live-healthy/when-is-your-baby-due",
    cover_image_url:
      "https://ch-api.healthhub.sg/api/public/content/8692c864101e4603868fb170c00230fe?v=534ae16e&t=livehealthyheaderimage",
  },
  {
    title: "Important Nutrients: What Should You Eat More Of?",
    description:
      "Important Nutrients: What Should You Eat More Of? Important Nutrients: What Should You Eat More Of? Important Nutrients: What Should You Eat More Of?",
    url: "https://www.healthhub.sg/live-healthy/important-nutrients-what-should-you-eat-more-of",
    cover_image_url:
      "https://ch-api.healthhub.sg/api/public/content/3885d0458c0a4521beb14ca352730423?v=646204cc&t=livehealthyheaderimage",
  },
];

@Component({
  selector: "app-text-input",
  standalone: true,
  imports: [
    LucideAngularModule,
    FormsModule,
    CommonModule,
    InputTextModule,
    Button,
    ReactiveFormsModule,
  ],
  templateUrl: "./text-input.component.html",
  styleUrl: "./text-input.component.css",
})
export class TextInputComponent implements OnInit {
  profile: BehaviorSubject<Profile | undefined> = new BehaviorSubject<
    Profile | undefined
  >(undefined);

  questionForm = new FormGroup({
    question: new FormControl(""),
  });

  constructor(
    private chatMessageService: ChatMessageService,
    private preferences: PreferenceService,
    private profileService: ProfileService,
    private route: ActivatedRoute
  ) {}

  ngOnInit() {
    this.profile = this.profileService.getProfile(
      this.route.snapshot.paramMap.get("profileId") as string
    );
  }

  setVoiceMode() {
    this.preferences.setChatMode(ChatMode.Voice);
  }

  sendMessage() {
    if (!this.questionForm.value.question) {
      return;
    }
    this.chatMessageService
      .insert({
        id: createId(),
        profile_id: this.profile?.value?.id || "general",
        role: MessageRole.User,
        timestamp: new Date().getTime(),
        message: this.questionForm.value.question || "",
      })
      .then(() => {
        this.questionForm.reset();
        console.log("here");
        this.sendSystemMessage();
      })
      .catch(console.error);
  }

  sendSystemMessage() {
    this.chatMessageService.insert({
      id: createId(),
      profile_id: this.profile?.value?.id || "general",
      role: MessageRole.System,
      timestamp: new Date().getTime(),
      message: "This is a mock response. This is a mock response. This is a mock response. This is a mock response. This is a mock response. This is a mock response. This is a mock response. This is a mock response. This is a mock response. This is a mock response. This is a mock response. This is a mock response. This is a mock response. This is a mock response. This is a mock response. This is a mock response. This is a mock response. This is a mock response. This is a mock response. This is a mock response. This is a mock response.",
      sources: sources,
    });
  }
}
