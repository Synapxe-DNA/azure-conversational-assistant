import { Component } from "@angular/core";
import { ProfileService } from "../../services/profile/profile.service";
import { createId } from "@paralleldrive/cuid2";
import { FormControl, FormGroup, Validators, AbstractControl, ValidationErrors } from "@angular/forms";
import { ProfileGender, ProfileType } from "../../types/profile.type";
import { CardModule } from "primeng/card";
import { InputTextModule } from "primeng/inputtext";
import { DropdownModule } from "primeng/dropdown";
import { SelectButtonModule } from "primeng/selectbutton";
import { InputNumberModule } from "primeng/inputnumber";
import { InputTextareaModule } from "primeng/inputtextarea";
import { ReactiveFormsModule } from "@angular/forms";
import { Button } from "primeng/button";
import { MessageService } from "primeng/api";
import { MultiSelectModule } from "primeng/multiselect";
import { PreferenceService } from "../../services/preference/preference.service";
import { ChatMode } from "../../types/chat-mode.type";
import { Router } from "@angular/router";
import { CommonModule } from "@angular/common";

@Component({
  selector: "app-create-profile",
  standalone: true,
  imports: [
    CommonModule,
    CardModule,
    ReactiveFormsModule,
    InputTextModule,
    DropdownModule,
    SelectButtonModule,
    InputNumberModule,
    InputTextareaModule,
    Button,
    MultiSelectModule
  ],
  templateUrl: "./create-profile.component.html",
  styleUrl: "./create-profile.component.css"
})
export class CreateProfileComponent {
  profileForm: FormGroup = new FormGroup({
    name: new FormControl<string>("", Validators.required),
    profile_type: new FormControl<ProfileType>(ProfileType.Myself, Validators.required),
    age: new FormControl<number | null>(null, [Validators.required, this.ageValidator]),
    gender: new FormControl<ProfileGender>(ProfileGender.Undefined, Validators.required),
    existing_condition: new FormControl<{ name: string; label: string }[]>([])
  });

  profileTypeOptions: { label: string; value: ProfileType }[] = [
    { label: "Myself", value: ProfileType.Myself },
    { label: "Others", value: ProfileType.Others }
  ];

  profileGenderOptions: ProfileGender[] = [ProfileGender.Male, ProfileGender.Female];

  profileConditionOptions: { name: string; label: string }[] = [
    { name: "Diabetes", label: "Diabetes" },
    { name: "Hypertension", label: "Hypertension" },
    { name: "High Cholesterol", label: "High Cholesterol" }
  ];

  constructor(
    private preferences: PreferenceService,
    private profileService: ProfileService,
    private toastService: MessageService,
    private router: Router
  ) {}

  // Custom validator to check if the age is greater than 100
  ageValidator(control: AbstractControl): ValidationErrors | null {
    const age = control.value;
    if (age !== null && age > 100) {
      return { invalidAge: true };
    }
    return null;
  }

  createProfile() {
    if (this.profileForm.valid) {
      this.profileService.createProfile({
        id: createId(),
        name: this.profileForm.value.name,
        profile_type: this.profileForm.value.profile_type,
        gender: this.profileForm.value.gender,
        age: this.profileForm.value.age as number,
        existing_conditions: this.profileForm.value.existing_condition.map((v: Record<string, string>) => v["label"]).join(", ")
      });
      this.toastService.add({
        severity: "success",
        summary: "Profile created!",
        detail: `Profile ${this.profileForm.value.name} has been created!`
      });
      this.preferences.$chatMode.next(ChatMode.Voice);
    }
  }
}
