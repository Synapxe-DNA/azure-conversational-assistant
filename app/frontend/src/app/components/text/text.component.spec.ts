import { ComponentFixture, TestBed } from "@angular/core/testing";

import { TextComponent } from "./text.component";
import { icons, LucideAngularModule } from "lucide-angular";
import { ChatMessageService } from "../../services/chat-message/chat-message.service";
import { ProfileService } from "../../services/profile/profile.service";
import { ActivatedRoute } from "@angular/router";
import { NgxIndexedDBModule, NgxIndexedDBService } from "ngx-indexed-db";
import { NgxIndexedDbConfig } from "../../configs/ngx-indexed-db/ngx-indexed-db.config";

describe("TextComponent", () => {
  let component: TextComponent;
  let fixture: ComponentFixture<TextComponent>;

  beforeEach(async () => {
    const activatedRouteMock = {
      snapshot: { paramMap: { get: () => "1234" } }
    };

    await TestBed.configureTestingModule({
      imports: [TextComponent, LucideAngularModule.pick(icons), NgxIndexedDBModule.forRoot(NgxIndexedDbConfig)],
      providers: [ChatMessageService, ProfileService, NgxIndexedDBService, { provide: ActivatedRoute, useValue: activatedRouteMock }]
    }).compileComponents();

    fixture = TestBed.createComponent(TextComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});
