import { Component, Input } from '@angular/core';
import { Message } from '../../../types/message.type';

@Component({
  selector: 'app-voice-message',
  standalone: true,
  imports: [],
  templateUrl: './voice-message.component.html',
  styleUrl: './voice-message.component.css'
})
export class VoiceMessageComponent {
  @Input() message!: string
}
