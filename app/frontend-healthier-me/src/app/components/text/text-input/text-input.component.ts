import {Component, OnInit} from '@angular/core';
import {MessageRole} from '../../../types/message.type';
import {LucideAngularModule} from 'lucide-angular';
import {FormControl, FormGroup, FormsModule, ReactiveFormsModule} from '@angular/forms';
import {CommonModule} from '@angular/common';
import {InputTextModule} from "primeng/inputtext";
import {ChatMessageService} from "../../../services/chat-message/chat-message.service";
import {createId} from "@paralleldrive/cuid2";
import {ProfileService} from "../../../services/profile/profile.service";
import {BehaviorSubject} from "rxjs";
import {Profile} from "../../../types/profile.type";
import {ActivatedRoute} from "@angular/router";
import {Button} from "primeng/button";
import {PreferenceService} from "../../../services/preference/preference.service";
import {ChatMode} from "../../../types/chat-mode.type";


@Component({
  selector: 'app-text-input',
  standalone: true,
  imports: [LucideAngularModule, FormsModule, CommonModule, InputTextModule, Button, ReactiveFormsModule],
  templateUrl: './text-input.component.html',
  styleUrl: './text-input.component.css'
})
export class TextInputComponent implements OnInit{
  profile:BehaviorSubject<Profile|undefined> = new BehaviorSubject<Profile|undefined>(undefined)

  questionForm = new FormGroup({
    "question": new FormControl("")
  })

  constructor(
    private chatMessageService: ChatMessageService,
    private preferences: PreferenceService,
    private profileService: ProfileService,
    private route: ActivatedRoute
  ) {
  }

  ngOnInit() {
    this.profile = this.profileService.getProfile(this.route.snapshot.paramMap.get('profileId') as string)
  }

  setVoiceMode(){
    this.preferences.setChatMode(ChatMode.Voice)
  }

  sendMessage() {
    if(!this.questionForm.value.question){
      return
    }
    this.chatMessageService.insert({
      id: createId(),
      profile_id: this.profile?.value?.id || "general",
      role: MessageRole.User,
      timestamp: new Date().getTime(),
      message: this.questionForm.value.question || ""
    })
      .then(()=>{
        this.questionForm.reset()
      })
      .catch(console.error)
  }

}
