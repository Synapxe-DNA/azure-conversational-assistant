import { ComponentFixture, TestBed } from "@angular/core/testing";

import { TextSystemComponent } from "./text-system.component";
import { MessageRole } from "../../../types/message.type";

describe("TextSystemComponent", () => {
    let component: TextSystemComponent;
    let fixture: ComponentFixture<TextSystemComponent>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [TextSystemComponent]
        }).compileComponents();

        fixture = TestBed.createComponent(TextSystemComponent);
        component = fixture.componentInstance;
        component.message = {
            id: "1234",
            profile_id: "1234profileId",
            timestamp: 1,
            role: MessageRole.Assistant,
            message: "test message",
            sources: [
                {
                    url: "some_url",
                    title: "title",
                    description: "description",
                    cover_image_url: "cover_image_url"
                }
            ]
        };
        fixture.detectChanges();
    });

    it("should create", () => {
        expect(component).toBeTruthy();
    });
});
