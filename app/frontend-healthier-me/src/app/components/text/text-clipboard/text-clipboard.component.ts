import { Component, Input } from '@angular/core';
import { Button } from 'primeng/button';

@Component({
  selector: 'app-text-clipboard',
  standalone: true,
  imports: [Button],
  templateUrl: './text-clipboard.component.html',
  styleUrl: './text-clipboard.component.css'
})
export class TextClipboardComponent {
  @Input() message?: string;


}
