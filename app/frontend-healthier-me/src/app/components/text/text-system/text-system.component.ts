import { Component, Input } from '@angular/core';
import { Message } from '../../../types/message.type';
import { TextSourceComponent } from '../text-source/text-source.component';

@Component({
  selector: 'app-text-system',
  standalone: true,
  imports: [TextSourceComponent],
  templateUrl: './text-system.component.html',
  styleUrl: './text-system.component.css'
})

export class TextSystemComponent {
  @Input() message!: Message

  
  
}
