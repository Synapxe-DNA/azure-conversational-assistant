import { AfterViewInit, Component, Input, OnInit } from "@angular/core";
import { GeneralProfile, Profile, ProfileGender } from "../../../types/profile.type";
import { ActivatedRoute, Router } from "@angular/router";
import { NgIf, NgOptimizedImage } from "@angular/common";
import { ContextMenuModule } from "primeng/contextmenu";
import { MenuItem, MenuItemCommandEvent, MessageService } from "primeng/api";
import { ProfileService } from "../../../services/profile/profile.service";

@Component({
  selector: "app-navbar-profile-link",
  standalone: true,
  imports: [NgOptimizedImage, ContextMenuModule, NgIf],
  templateUrl: "./navbar-profile-link.component.html",
  styleUrl: "./navbar-profile-link.component.css"
})
export class NavbarProfileLinkComponent implements OnInit {
  @Input() profile!: Profile;
  @Input() onCloseSidebar?: () => void; // Accept the function from the parent

  isActive: boolean = false;
  gender: string = "";

  contextMenuItems: MenuItem[] = [
    {
      label: "Delete",
      command: () => {
        if (this.profile.id) {
          this.profileService.deleteProfile(this.profile.id);
          this.toastService.add({
            severity: "warn",
            summary: "Profile deleted!",
            detail: `${this.profile.name} has been deleted.`
          });
        }
      }
    }
  ];

  constructor(
    private router: Router,
    private profileService: ProfileService,
    private toastService: MessageService
  ) {}

  ngOnInit() {
    const currentPath = this.router.url.split("/");

    if (currentPath.length >= 3 && currentPath[1] === "chat") {
      if (currentPath[2] === this.profile.id || (currentPath[2] === "general" && !this.profile.id)) {
        this.isActive = true;
      }
    }
  }

  getProfileDescription(): string {
    if (this.profile.id === GeneralProfile.id) {
      return "No profile set";
    }
    this.gender = this.profile.gender === ProfileGender.Undefined ? "" : this.profile.gender;
    return `${this.profile.gender === ProfileGender.Undefined ? "" : this.profile.gender + ","} ${this.profile.age} years old`;
  }

  onEditProfile(profileId: string) {
    // Navigate to the edit profile page with the profile ID
    this.router.navigate([`/edit-profile/${profileId}`]);
    if (this.onCloseSidebar) {
      this.onCloseSidebar();
    }
  }
}
