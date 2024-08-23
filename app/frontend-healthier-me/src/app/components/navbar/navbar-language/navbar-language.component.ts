import { CommonModule } from '@angular/common';
import { Component, OnInit, Input } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { DropdownModule } from 'primeng/dropdown';
import { PreferenceService } from '../../../services/preference/preference.service';
import { Language } from '../../../types/language.type';



@Component({
  selector: "app-navbar-language",
  standalone: true,
  imports: [DropdownModule, FormsModule, ReactiveFormsModule, CommonModule],
  templateUrl: "./navbar-language.component.html",
  styleUrl: "./navbar-language.component.css",
})
export class NavbarLanguageComponent implements OnInit {
  
  languageOptions!: string[] 
  chosenLanguage: string 

  constructor(
    private preference: PreferenceService,
  ) {
    this.chosenLanguage = preference.$language.value.valueOf()
    console.log("chosen language init " + this.chosenLanguage)
  }

  ngOnInit(): void {
    this.languageOptions = Object.values(Language)
  }

  setLanguage(chosenLanguage: string) {
    console.log("setLanguage", chosenLanguage)
    switch (chosenLanguage) {
      case "ENGLISH":
        this.preference.setLanguage(Language.English)
        break;
      
        case "SPOKEN":
          this.preference.setLanguage(Language.Spoken)
          break;

          case "CHINESE":
        this.preference.setLanguage(Language.Chinese)
        break;

        case "MALAY":
        this.preference.setLanguage(Language.Malay)
        break;

        case "TAMIL":
        this.preference.setLanguage(Language.Tamil)
        break;
      default:
        break;
    }
  }

}
