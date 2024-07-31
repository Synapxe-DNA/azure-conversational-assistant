import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MicrophoneButtonComponent } from './microphone-button.component';
import {icons, LucideAngularModule} from "lucide-angular";

describe('MicrophoneButtonComponent', () => {
  let component: MicrophoneButtonComponent;
  let fixture: ComponentFixture<MicrophoneButtonComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MicrophoneButtonComponent, LucideAngularModule.pick(icons),]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MicrophoneButtonComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
