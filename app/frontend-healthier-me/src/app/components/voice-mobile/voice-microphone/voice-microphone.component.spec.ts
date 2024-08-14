import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VoiceMicrophoneComponent } from './voice-microphone.component';

describe('VoiceMicrophoneComponent', () => {
  let component: VoiceMicrophoneComponent;
  let fixture: ComponentFixture<VoiceMicrophoneComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VoiceMicrophoneComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VoiceMicrophoneComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
