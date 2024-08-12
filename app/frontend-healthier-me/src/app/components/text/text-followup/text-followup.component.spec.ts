import { ComponentFixture, TestBed } from "@angular/core/testing";

import { TextFollowupComponent } from "./text-followup.component";

describe("TextFollowupComponent", () => {
  let component: TextFollowupComponent;
  let fixture: ComponentFixture<TextFollowupComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TextFollowupComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(TextFollowupComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});
