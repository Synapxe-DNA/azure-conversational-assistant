import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TextMobileComponent } from './text-mobile.component';

describe('TextMobileComponent', () => {
  let component: TextMobileComponent;
  let fixture: ComponentFixture<TextMobileComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TextMobileComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TextMobileComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
