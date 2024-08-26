import { Component, OnInit } from "@angular/core";
import { MessageRole, MessageSource } from "../../../types/message.type";
import { LucideAngularModule } from "lucide-angular";
import { FormControl, FormGroup, FormsModule, ReactiveFormsModule } from "@angular/forms";
import { CommonModule } from "@angular/common";
import { InputTextModule } from "primeng/inputtext";
import { ChatMessageService } from "../../../services/chat-message/chat-message.service";
import { createId } from "@paralleldrive/cuid2";
import { ProfileService } from "../../../services/profile/profile.service";
import { BehaviorSubject, takeWhile } from "rxjs";
import { GeneralProfile, Profile } from "../../../types/profile.type";
import { ActivatedRoute } from "@angular/router";
import { Button } from "primeng/button";
import { PreferenceService } from "../../../services/preference/preference.service";
import { ChatMode } from "../../../types/chat-mode.type";
import { ConvoBrokerService } from "../../../services/convo-broker/convo-broker.service";

@Component({
    selector: "app-text-input",
    standalone: true,
    imports: [LucideAngularModule, FormsModule, CommonModule, InputTextModule, Button, ReactiveFormsModule],
    templateUrl: "./text-input.component.html",
    styleUrl: "./text-input.component.css"
})
export class TextInputComponent implements OnInit {
    profile: BehaviorSubject<Profile | undefined> = new BehaviorSubject<Profile | undefined>(undefined);

    questionForm = new FormGroup({
        question: new FormControl("")
    });

    constructor(
        private convoBroker: ConvoBrokerService,
        private preferences: PreferenceService,
        private profileService: ProfileService,
        private route: ActivatedRoute
    ) {}

    ngOnInit() {
        this.route.paramMap
            .pipe(
                takeWhile(p => {
                    return p.get("profileId") !== undefined;
                }, true)
            )
            .subscribe(p => {
                this.profile = this.profileService.getProfile(p.get("profileId")!);
            });
    }

    setVoiceMode() {
        this.preferences.setChatMode(ChatMode.Voice);
    }

    sendMessage() {
        if (!this.questionForm.value.question) {
            return;
        }

        this.convoBroker
            .sendChat(this.questionForm.value.question, this.profile.value || GeneralProfile)
            .then(() => {
                this.questionForm.reset();
            })
            .catch(console.error);
    }
}
