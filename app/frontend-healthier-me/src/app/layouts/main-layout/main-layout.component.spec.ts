import { ComponentFixture, TestBed } from "@angular/core/testing"

import { MainLayoutComponent } from "./main-layout.component"
import {NgxIndexedDbConfig} from "../../configs/ngx-indexed-db/ngx-indexed-db.config";
import {NgxIndexedDBModule, NgxIndexedDBService} from "ngx-indexed-db";
import {ProfileService} from "../../services/profile/profile.service";
import {MessageService} from "primeng/api";
import {ToastModule} from "primeng/toast";
import {icons, LucideAngularModule} from "lucide-angular";

describe("MainLayoutComponent", () => {
  let component: MainLayoutComponent
  let fixture: ComponentFixture<MainLayoutComponent>

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MainLayoutComponent, NgxIndexedDBModule.forRoot(NgxIndexedDbConfig), ToastModule, LucideAngularModule.pick(icons),],
      providers: [ProfileService, NgxIndexedDBService, MessageService]
    }).compileComponents()

    fixture = TestBed.createComponent(MainLayoutComponent)
    component = fixture.componentInstance
    fixture.detectChanges()
  })

  it("should create", () => {
    expect(component).toBeTruthy()
  })
})
