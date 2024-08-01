import { ComponentFixture, TestBed } from "@angular/core/testing"

import { NavbarProfileLinkComponent } from "./navbar-profile-link.component"
import {NgxIndexedDBModule, NgxIndexedDBService} from "ngx-indexed-db";
import {ProfileService} from "../../../services/profile/profile.service";
import {NgxIndexedDbConfig} from "../../../configs/ngx-indexed-db/ngx-indexed-db.config";
import {MessageService} from "primeng/api";
import {GeneralProfile} from "../../../types/profile.type";

describe("NavbarProfileLinksComponent", () => {
  let component: NavbarProfileLinkComponent
  let fixture: ComponentFixture<NavbarProfileLinkComponent>

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NavbarProfileLinkComponent, NgxIndexedDBModule.forRoot(NgxIndexedDbConfig)],
      providers: [ProfileService, NgxIndexedDBService, MessageService]
    }).compileComponents()

    fixture = TestBed.createComponent(NavbarProfileLinkComponent)
    component = fixture.componentInstance
    component.profile = GeneralProfile
    fixture.detectChanges()
  })

  it("should create", () => {
    expect(component).toBeTruthy()
  })
})
