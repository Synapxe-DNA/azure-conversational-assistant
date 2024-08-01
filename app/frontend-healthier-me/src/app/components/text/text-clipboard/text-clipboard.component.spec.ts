import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TextClipboardComponent } from './text-clipboard.component';

describe('TextClipboardComponent', () => {
  let component: TextClipboardComponent;
  let fixture: ComponentFixture<TextClipboardComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TextClipboardComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TextClipboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
