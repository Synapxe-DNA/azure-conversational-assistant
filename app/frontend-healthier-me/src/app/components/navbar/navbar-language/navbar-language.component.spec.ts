import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NavbarLanguageComponent } from './navbar-language.component';

describe('NavbarLanguageComponent', () => {
  let component: NavbarLanguageComponent;
  let fixture: ComponentFixture<NavbarLanguageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NavbarLanguageComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(NavbarLanguageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
