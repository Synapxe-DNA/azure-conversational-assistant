import { TestBed } from "@angular/core/testing"

import { ProfileService } from "./profile.service"
import {NgxIndexedDBModule, NgxIndexedDBService} from "ngx-indexed-db";
import {NgxIndexedDbConfig} from "../../configs/ngx-indexed-db/ngx-indexed-db.config";

describe("ProfileService", () => {
  let service: ProfileService

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [NgxIndexedDBModule.forRoot(NgxIndexedDbConfig)],
      providers: [
        ProfileService,
        NgxIndexedDBService
      ]
    })
    service = TestBed.inject(ProfileService)
  })

  it("should be created", () => {
    expect(service).toBeTruthy()
  })
})
