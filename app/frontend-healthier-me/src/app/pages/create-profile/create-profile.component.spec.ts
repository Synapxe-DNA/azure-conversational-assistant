import { ComponentFixture, TestBed } from "@angular/core/testing"

import { CreateProfileComponent } from "./create-profile.component"
import {ProfileService} from "../../services/profile/profile.service";
import {NgxIndexedDBModule, NgxIndexedDBService} from "ngx-indexed-db";
import {NgxIndexedDbConfig} from "../../configs/ngx-indexed-db/ngx-indexed-db.config";
import {MessageService} from "primeng/api";

describe("CreateProfileComponent", () => {
  let component: CreateProfileComponent
  let fixture: ComponentFixture<CreateProfileComponent>

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CreateProfileComponent, NgxIndexedDBModule.forRoot(NgxIndexedDbConfig)],
      providers: [ProfileService, NgxIndexedDBService, MessageService]
    }).compileComponents()

    fixture = TestBed.createComponent(CreateProfileComponent)
    component = fixture.componentInstance
    fixture.detectChanges()
  })

  it("should create", () => {
    expect(component).toBeTruthy()
  })
})
