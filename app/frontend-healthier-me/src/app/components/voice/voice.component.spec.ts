import { ComponentFixture, TestBed } from "@angular/core/testing"

import { VoiceComponent } from "./voice.component"
import {icons, LucideAngularModule} from "lucide-angular";
import {PreferenceService} from "../../services/preference/preference.service";

describe("VoiceComponent", () => {
  let component: VoiceComponent
  let fixture: ComponentFixture<VoiceComponent>

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VoiceComponent, LucideAngularModule.pick(icons)],
      providers: [PreferenceService]
    }).compileComponents()

    fixture = TestBed.createComponent(VoiceComponent)
    component = fixture.componentInstance
    fixture.detectChanges()
  })

  it("should create", () => {
    expect(component).toBeTruthy()
  })
})
