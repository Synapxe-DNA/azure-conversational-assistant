import { ComponentFixture, TestBed } from "@angular/core/testing"

import { TextComponent } from "./text.component"
import {icons, LucideAngularModule} from "lucide-angular";

describe("TextComponent", () => {
  let component: TextComponent
  let fixture: ComponentFixture<TextComponent>

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TextComponent, LucideAngularModule.pick(icons)],
    }).compileComponents()

    fixture = TestBed.createComponent(TextComponent)
    component = fixture.componentInstance
    fixture.detectChanges()
  })

  it("should create", () => {
    expect(component).toBeTruthy()
  })
})
