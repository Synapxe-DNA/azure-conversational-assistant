import { ChangeDetectorRef, Component, OnInit } from "@angular/core";
import { NavbarLogoGroupComponent } from "../navbar/navbar-logo-group/navbar-logo-group.component";
import { NavbarLineComponent } from "../navbar/navbar-line/navbar-line.component";
import { NavbarProfileLinkComponent } from "../navbar/navbar-profile-links/navbar-profile-link.component";
import { NavbarProfileCreateComponent } from "../navbar/navbar-profile-create/navbar-profile-create.component";
import { GeneralProfile, Profile } from "../../types/profile.type";
import { ProfileService } from "../../services/profile/profile.service";
import { NavbarLanguageComponent } from "../navbar/navbar-language/navbar-language.component";
import { Button } from "primeng/button";
import { CommonModule } from "@angular/common";
import { PreferenceService } from "../../services/preference/preference.service";
import { ChatMode } from "../../types/chat-mode.type";
import { SidebarModule } from "primeng/sidebar";
import { NavbarComponent } from "../navbar/navbar.component";
import { LucideAngularModule } from "lucide-angular";

@Component({
  selector: "app-navbar-mobile",
  standalone: true,
  imports: [
    NavbarLogoGroupComponent,
    NavbarLineComponent,
    NavbarProfileLinkComponent,
    NavbarProfileCreateComponent,
    NavbarLanguageComponent,
    NavbarComponent,
    CommonModule,
    SidebarModule,
    LucideAngularModule,
    Button,
  ],
  templateUrl: "./navbar-mobile.component.html",
  styleUrl: "./navbar-mobile.component.css",
})
export class NavbarMobileComponent implements OnInit {
  chatMode?: ChatMode;
  profiles: Profile[] = [];
  sidebar: boolean = false;
  firstLoad: boolean = true;

  constructor(
    private profileService: ProfileService,
    private cdr: ChangeDetectorRef,
    private preferences: PreferenceService,
  ) {
    this.preferences.$chatMode.subscribe((m) => {
      this.chatMode = m;
    });
  }

  ngOnInit() {
    this.profileService.getProfiles().subscribe((v) => {
      this.profiles = v;
      this.cdr.markForCheck();
    });
  }

  toggleSidebar() {
    this.sidebar = !this.sidebar;
    this.firstLoad = false;
  }

  closeSidebar() {
    this.sidebar = false;
  }

  toggleChatMode() {
    switch (this.chatMode) {
      case ChatMode.Voice:
        this.preferences.setChatMode(ChatMode.Text);
        break;
      case ChatMode.Text:
        this.preferences.setChatMode(ChatMode.Voice);
        break;
    }
  }

  protected readonly GeneralProfile = GeneralProfile;
  protected readonly ChatMode = ChatMode;
}
