import { ComponentFixture, TestBed } from "@angular/core/testing";

import { TextUserComponent } from "./text-user.component";
import { MessageRole } from "../../../types/message.type";

describe("TextUserComponent", () => {
  let component: TextUserComponent;
  let fixture: ComponentFixture<TextUserComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TextUserComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(TextUserComponent);
    component = fixture.componentInstance;
    component.message = {
      id: "123",
      timestamp: 1,
      profile_id: "123",
      role: MessageRole.User,
      message: "testing message",
    };
    fixture.detectChanges();
  });

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});
