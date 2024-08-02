import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TextShowSourceComponent } from './text-show-source.component';

describe('TextShowSourceComponent', () => {
  let component: TextShowSourceComponent;
  let fixture: ComponentFixture<TextShowSourceComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TextShowSourceComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TextShowSourceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
