import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VoiceSourcesComponent } from './voice-sources.component';

describe('VoiceSourcesComponent', () => {
  let component: VoiceSourcesComponent;
  let fixture: ComponentFixture<VoiceSourcesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VoiceSourcesComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VoiceSourcesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
