import { ComponentFixture, TestBed } from "@angular/core/testing";

import { ChatComponent } from "./chat.component";
import { icons, LucideAngularModule } from "lucide-angular";
import { NgxIndexedDBModule, NgxIndexedDBService } from "ngx-indexed-db";
import { NgxIndexedDbConfig } from "../../configs/ngx-indexed-db/ngx-indexed-db.config";
import { ActivatedRoute } from "@angular/router";

describe("ChatComponent", () => {
  let component: ChatComponent;
  let fixture: ComponentFixture<ChatComponent>;

  beforeEach(async () => {
    const activatedRouteMock = {
      snapshot: { paramMap: { get: () => "1234" } },
    };

    await TestBed.configureTestingModule({
      imports: [
        ChatComponent,
        LucideAngularModule.pick(icons),
        NgxIndexedDBModule.forRoot(NgxIndexedDbConfig),
      ],
      providers: [
        NgxIndexedDBService,
        { provide: ActivatedRoute, useValue: activatedRouteMock },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ChatComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});
