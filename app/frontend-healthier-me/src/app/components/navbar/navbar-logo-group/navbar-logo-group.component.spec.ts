import { ComponentFixture, TestBed } from "@angular/core/testing";

import { NavbarLogoGroupComponent } from "./navbar-logo-group.component";

describe("NavbarLogoGroupComponent", () => {
  let component: NavbarLogoGroupComponent;
  let fixture: ComponentFixture<NavbarLogoGroupComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NavbarLogoGroupComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(NavbarLogoGroupComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});
