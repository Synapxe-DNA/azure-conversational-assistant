import { Component, OnInit, HostListener } from "@angular/core";
import { RouterOutlet } from "@angular/router";
import { NavbarComponent } from "../../components/navbar/navbar.component";
import { NavbarMobileComponent } from "../../components/navbar-mobile/navbar-mobile.component";
import { DisclaimerComponent } from "../../components/components/disclaimer/disclaimer.component";

@Component({
  selector: "app-main-layout",
  standalone: true,
  imports: [RouterOutlet, NavbarComponent, NavbarMobileComponent, DisclaimerComponent],
  templateUrl: "./main-layout.component.html",
  styleUrls: ["./main-layout.component.css"]
})
export class MainLayoutComponent implements OnInit {
  isMobile?: boolean;
  isDisclaimerVisible: boolean = false;

  ngOnInit(): void {
    this.checkViewport();
  }

  @HostListener("window:resize", ["$event"])
  onResize(event: any) {
    this.checkViewport();
  }

  checkViewport() {
    this.isMobile = window.innerWidth < 768; // Adjust this value as needed
  }
}
