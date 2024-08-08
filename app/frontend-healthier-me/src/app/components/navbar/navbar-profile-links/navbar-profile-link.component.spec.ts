import { ComponentFixture, TestBed } from "@angular/core/testing";

import { NavbarProfileLinkComponent } from "./navbar-profile-link.component";
import { NgxIndexedDBModule, NgxIndexedDBService } from "ngx-indexed-db";
import { ProfileService } from "../../../services/profile/profile.service";
import { NgxIndexedDbConfig } from "../../../configs/ngx-indexed-db/ngx-indexed-db.config";
import { MessageService } from "primeng/api";
import { GeneralProfile } from "../../../types/profile.type";
import { ActivatedRoute } from "@angular/router";

describe("NavbarProfileLinksComponent", () => {
  let component: NavbarProfileLinkComponent;
  let fixture: ComponentFixture<NavbarProfileLinkComponent>;

  beforeEach(async () => {
    const activatedRouteMock = {
      snapshot: { paramMap: { get: () => "1234" } },
    };

    await TestBed.configureTestingModule({
      imports: [
        NavbarProfileLinkComponent,
        NgxIndexedDBModule.forRoot(NgxIndexedDbConfig),
      ],
      providers: [
        ProfileService,
        NgxIndexedDBService,
        MessageService,
        { provide: ActivatedRoute, useValue: activatedRouteMock },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(NavbarProfileLinkComponent);
    component = fixture.componentInstance;
    component.profile = GeneralProfile;
    fixture.detectChanges();
  });

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});
