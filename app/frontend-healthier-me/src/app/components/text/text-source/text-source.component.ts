import { Component, Input } from '@angular/core';
import { MessageSource } from '../../../types/message.type';

@Component({
  selector: 'app-text-source',
  standalone: true,
  imports: [],
  templateUrl: './text-source.component.html',
  styleUrl: './text-source.component.css'
})
export class TextSourceComponent {
  @Input() sources?: MessageSource[];
}
