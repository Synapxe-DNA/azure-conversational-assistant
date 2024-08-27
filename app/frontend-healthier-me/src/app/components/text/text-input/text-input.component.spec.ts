import { ComponentFixture, TestBed } from "@angular/core/testing";

import { TextInputComponent } from "./text-input.component";
import { NgxIndexedDBModule, NgxIndexedDBService } from "ngx-indexed-db";
import { NgxIndexedDbConfig } from "../../../configs/ngx-indexed-db/ngx-indexed-db.config";
import { icons, LucideAngularModule } from "lucide-angular";
import { ReactiveFormsModule } from "@angular/forms";
import { ChatMessageService } from "../../../services/chat-message/chat-message.service";
import { ProfileService } from "../../../services/profile/profile.service";
import { PreferenceService } from "../../../services/preference/preference.service";
import { ActivatedRoute } from "@angular/router";

describe("TextInputComponent", () => {
  let component: TextInputComponent;
  let fixture: ComponentFixture<TextInputComponent>;

  beforeEach(async () => {
    const activatedRouteMock = {
      snapshot: { paramMap: { get: () => "1234" } }
    };

    await TestBed.configureTestingModule({
      imports: [TextInputComponent, NgxIndexedDBModule.forRoot(NgxIndexedDbConfig), LucideAngularModule.pick(icons), ReactiveFormsModule],
      providers: [ChatMessageService, ProfileService, PreferenceService, { provide: ActivatedRoute, useValue: activatedRouteMock }]
    }).compileComponents();

    fixture = TestBed.createComponent(TextInputComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});
