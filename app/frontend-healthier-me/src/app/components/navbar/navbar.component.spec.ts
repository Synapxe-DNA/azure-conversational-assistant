import { ComponentFixture, TestBed } from "@angular/core/testing"

import { NavbarComponent } from "./navbar.component"
import {NgxIndexedDBModule, NgxIndexedDBService} from "ngx-indexed-db";
import {NgxIndexedDbConfig} from "../../configs/ngx-indexed-db/ngx-indexed-db.config";
import {ProfileService} from "../../services/profile/profile.service";
import {MessageService} from "primeng/api";
import {icons, LucideAngularModule} from "lucide-angular";

describe("NavbarComponent", () => {
  let component: NavbarComponent
  let fixture: ComponentFixture<NavbarComponent>

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NavbarComponent, NgxIndexedDBModule.forRoot(NgxIndexedDbConfig), LucideAngularModule.pick(icons),],
      providers: [ProfileService, NgxIndexedDBService, MessageService],
    }).compileComponents()

    fixture = TestBed.createComponent(NavbarComponent)
    component = fixture.componentInstance
    fixture.detectChanges()
  })

  it("should create", () => {
    expect(component).toBeTruthy()
  })
})
