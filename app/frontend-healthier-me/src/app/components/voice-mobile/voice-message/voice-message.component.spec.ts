import { ComponentFixture, TestBed } from "@angular/core/testing";

import { VoiceMessageComponent } from "./voice-message.component";

describe("VoiceMessageComponent", () => {
  let component: VoiceMessageComponent;
  let fixture: ComponentFixture<VoiceMessageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VoiceMessageComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(VoiceMessageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});
