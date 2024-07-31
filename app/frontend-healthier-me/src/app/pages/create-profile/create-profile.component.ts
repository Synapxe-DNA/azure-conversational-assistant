import { Component, OnInit } from "@angular/core"
import { ProfileService } from "../../services/profile/profile.service"
import { createId } from "@paralleldrive/cuid2"
import {FormBuilder, FormControl, FormGroup, ReactiveFormsModule} from "@angular/forms";
import {ProfileGender, ProfileType} from "../../types/profile.type";
import {CardModule} from "primeng/card";
import {InputTextModule} from "primeng/inputtext";
import {DropdownModule} from "primeng/dropdown";
import {SelectButtonModule} from "primeng/selectbutton";
import {InputNumberModule} from "primeng/inputnumber";
import {InputTextareaModule} from "primeng/inputtextarea";
import {Button} from "primeng/button";
import {MessageService} from "primeng/api";

@Component({
  selector: "app-create-profile",
  standalone: true,
  imports: [
    CardModule,
    ReactiveFormsModule,
    InputTextModule,
    DropdownModule,
    SelectButtonModule,
    InputNumberModule,
    InputTextareaModule,
    Button
  ],
  templateUrl: "./create-profile.component.html",
  styleUrl: "./create-profile.component.css",
})
export class CreateProfileComponent {


  profileForm:FormGroup = new FormGroup({
    name: new FormControl<string>(''),
    profile_type: new FormControl<ProfileType>(ProfileType.Myself),
    age: new FormControl<number|null>(null),
    gender: new FormControl<ProfileGender>(ProfileGender.Undefined),
    existing_condition: new FormControl<string>("")
  })

  profileTypeOptions:{label:string, value:ProfileType}[] = [
    {label: "Myself", value: ProfileType.Myself},
    {label: "Someone else", value: ProfileType.Others},
  ]

  profileGenderOptions:ProfileGender[] = [
    ProfileGender.Male,
    ProfileGender.Female
  ]

  constructor(
    private profileService: ProfileService,
    private toastService: MessageService
  ) {}


  createProfile(){
    if(
      this.profileForm.value.name &&
      this.profileForm.value.profile_type &&
      this.profileForm.value.age &&
      this.profileForm.value.gender
    ){
      this.profileService.createProfile({
        id: createId(),
        name: this.profileForm.value.name,
        profile_type: this.profileForm.value.profile_type,
        gender: this.profileForm.value.gender,
        age: this.profileForm.value.age as number,
        existing_conditions: this.profileForm.value.existing_condition,
      })
      this.toastService.add({
        severity: 'success', summary: 'Profile created!', detail: `Profile ${this.profileForm.value.name} has been created!`
      })
    }
  }
}
