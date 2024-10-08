import { ChangeDetectorRef, Component, OnInit, HostListener } from "@angular/core";
import { NavbarLogoGroupComponent } from "./navbar-logo-group/navbar-logo-group.component";
import { NavbarLineComponent } from "./navbar-line/navbar-line.component";
import { NavbarProfileLinkComponent } from "./navbar-profile-links/navbar-profile-link.component";
import { NavbarProfileCreateComponent } from "./navbar-profile-create/navbar-profile-create.component";
import { GeneralProfile, Profile } from "../../types/profile.type";
import { ProfileService } from "../../services/profile/profile.service";
import { NavbarLanguageComponent } from "./navbar-language/navbar-language.component";

@Component({
  selector: "app-navbar",
  standalone: true,
  imports: [NavbarLogoGroupComponent, NavbarLineComponent, NavbarProfileLinkComponent, NavbarProfileCreateComponent, NavbarLanguageComponent],
  templateUrl: "./navbar.component.html",
  styleUrl: "./navbar.component.css"
})
export class NavbarComponent implements OnInit {
  profiles: Profile[] = [];
  sidebarOpen: boolean = false;

  constructor(
    private profileService: ProfileService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit() {
    this.profileService.getProfiles().subscribe(v => {
      this.profiles = v;
      this.cdr.markForCheck();
    });
  }

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }

  protected readonly GeneralProfile = GeneralProfile;
}
