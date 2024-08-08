import { ComponentFixture, TestBed } from "@angular/core/testing";

import { NavbarComponent } from "./navbar.component";
import { NgxIndexedDBModule, NgxIndexedDBService } from "ngx-indexed-db";
import { NgxIndexedDbConfig } from "../../configs/ngx-indexed-db/ngx-indexed-db.config";
import { ProfileService } from "../../services/profile/profile.service";
import { MessageService } from "primeng/api";
import { icons, LucideAngularModule } from "lucide-angular";
import { ActivatedRoute } from "@angular/router";

describe("NavbarComponent", () => {
  let component: NavbarComponent;
  let fixture: ComponentFixture<NavbarComponent>;

  beforeEach(async () => {
    const activatedRouteMock = {
      snapshot: { paramMap: { get: () => "1234" } },
    };

    await TestBed.configureTestingModule({
      imports: [
        NavbarComponent,
        NgxIndexedDBModule.forRoot(NgxIndexedDbConfig),
        LucideAngularModule.pick(icons),
      ],
      providers: [
        ProfileService,
        NgxIndexedDBService,
        MessageService,
        { provide: ActivatedRoute, useValue: activatedRouteMock },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(NavbarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});
