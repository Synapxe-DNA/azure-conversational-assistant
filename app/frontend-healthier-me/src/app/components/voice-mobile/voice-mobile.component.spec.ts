import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VoiceMobileComponent } from './voice-mobile.component';

describe('VoiceMobileComponent', () => {
  let component: VoiceMobileComponent;
  let fixture: ComponentFixture<VoiceMobileComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VoiceMobileComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VoiceMobileComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
