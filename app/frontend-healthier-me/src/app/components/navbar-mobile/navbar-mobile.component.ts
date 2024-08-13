import {
  ChangeDetectorRef,
  Component,
  OnInit,
} from "@angular/core";
import { NavbarLogoGroupComponent } from "../navbar/navbar-logo-group/navbar-logo-group.component";
import { NavbarLineComponent } from "../navbar/navbar-line/navbar-line.component";
import { NavbarProfileLinkComponent } from "../navbar/navbar-profile-links/navbar-profile-link.component";
import { NavbarProfileCreateComponent } from "../navbar/navbar-profile-create/navbar-profile-create.component";
import { GeneralProfile, Profile } from "../../types/profile.type";
import { ProfileService } from "../../services/profile/profile.service";
import { NavbarLanguageComponent } from "../navbar/navbar-language/navbar-language.component";
import { Button } from "primeng/button";
import { CommonModule } from "@angular/common";

@Component({
  selector: 'app-navbar-mobile',
  standalone: true,
  imports: [
    NavbarLogoGroupComponent,
    NavbarLineComponent,
    NavbarProfileLinkComponent,
    NavbarProfileCreateComponent,
    NavbarLanguageComponent,
    Button,
    CommonModule
  ],
  templateUrl: './navbar-mobile.component.html',
  styleUrl: './navbar-mobile.component.css'
})
export class NavbarMobileComponent implements OnInit{
  profiles: Profile[] = [];
  sidebar: boolean = false;

  constructor(
    private profileService: ProfileService,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit() {
    this.profileService.getProfiles().subscribe((v) => {
      this.profiles = v;
      this.cdr.markForCheck();
    });
  }

  toggleSidebar() {
    this.sidebar = !this.sidebar;
  }
  
  closeSidebar() {
    this.sidebar = false;
  }

  protected readonly GeneralProfile = GeneralProfile;
}
