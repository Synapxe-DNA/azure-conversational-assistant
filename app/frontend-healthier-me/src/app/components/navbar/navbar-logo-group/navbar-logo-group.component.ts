import { NgOptimizedImage } from "@angular/common";
import { Component } from "@angular/core";

@Component({
  selector: "app-navbar-logo-group",
  standalone: true,
  imports: [NgOptimizedImage],
  templateUrl: "./navbar-logo-group.component.html",
  styleUrl: "./navbar-logo-group.component.css"
})
export class NavbarLogoGroupComponent {}
