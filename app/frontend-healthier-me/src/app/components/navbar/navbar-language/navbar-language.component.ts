import { CommonModule } from '@angular/common';
import { Component, Output } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { DropdownModule } from 'primeng/dropdown';

interface Map {
  [key: string]: string | undefined
}

@Component({
  selector: 'app-navbar-language',
  standalone: true,
  imports: [
    DropdownModule,
    FormsModule,
    ReactiveFormsModule,
    CommonModule,
  ],
  templateUrl: './navbar-language.component.html',
  styleUrl: './navbar-language.component.css'
})
export class NavbarLanguageComponent {
  languages: Map = {'en-US': "English", 'en-GB': "English", "hi": "Hindi", "ms": "Malay", "zh": "Chinese"};
  languageOptions: string[] = ["English", "Chinese", "Malay", "Hindi"]
  @Output() language: string = this.languages[navigator.language] || "English"

}
