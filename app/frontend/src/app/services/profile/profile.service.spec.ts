import { TestBed } from "@angular/core/testing";

import { ProfileService } from "./profile.service";
import { NgxIndexedDBModule, NgxIndexedDBService } from "ngx-indexed-db";
import { NgxIndexedDbConfig } from "../../configs/ngx-indexed-db/ngx-indexed-db.config";
import { ActivatedRoute } from "@angular/router";

describe("ProfileService", () => {
  let service: ProfileService;

  beforeEach(() => {
    const activatedRouteMock = {
      snapshot: { paramMap: { get: () => "1234" } }
    };

    TestBed.configureTestingModule({
      imports: [NgxIndexedDBModule.forRoot(NgxIndexedDbConfig)],
      providers: [ProfileService, NgxIndexedDBService, { provide: ActivatedRoute, useValue: activatedRouteMock }]
    });
    service = TestBed.inject(ProfileService);
  });

  it("should be created", () => {
    expect(service).toBeTruthy();
  });
});
