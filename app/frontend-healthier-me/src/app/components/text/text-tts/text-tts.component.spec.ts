import { ComponentFixture, TestBed } from "@angular/core/testing";

import { TextTtsComponent } from "./text-tts.component";

describe("TextTtsComponent", () => {
    let component: TextTtsComponent;
    let fixture: ComponentFixture<TextTtsComponent>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [TextTtsComponent]
        }).compileComponents();

        fixture = TestBed.createComponent(TextTtsComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it("should create", () => {
        expect(component).toBeTruthy();
    });
});
