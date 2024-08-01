import { ComponentFixture, TestBed } from "@angular/core/testing"

import { NavbarProfileCreateComponent } from "./navbar-profile-create.component"
import {icons, LucideAngularModule} from "lucide-angular";
import {ProfileService} from "../../../services/profile/profile.service";
import {NgxIndexedDBService} from "ngx-indexed-db";

describe("NavbarProfileCreateComponent", () => {
  let component: NavbarProfileCreateComponent
  let fixture: ComponentFixture<NavbarProfileCreateComponent>

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        NavbarProfileCreateComponent,
        LucideAngularModule.pick(icons),
      ],
      providers: [
        NgxIndexedDBService, ProfileService
      ]
    }).compileComponents()

    fixture = TestBed.createComponent(NavbarProfileCreateComponent)
    component = fixture.componentInstance
    fixture.detectChanges()
  })

  it("should create", () => {
    expect(component).toBeTruthy()
  })
})
