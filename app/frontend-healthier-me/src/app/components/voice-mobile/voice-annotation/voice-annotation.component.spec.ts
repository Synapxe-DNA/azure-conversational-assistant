import { ComponentFixture, TestBed } from "@angular/core/testing";

import { VoiceAnnotationComponent } from "./voice-annotation.component";

describe("VoiceAnnotationComponent", () => {
  let component: VoiceAnnotationComponent;
  let fixture: ComponentFixture<VoiceAnnotationComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VoiceAnnotationComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(VoiceAnnotationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});
