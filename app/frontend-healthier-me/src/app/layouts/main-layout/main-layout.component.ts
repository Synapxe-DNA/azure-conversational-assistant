import { Component, OnInit } from "@angular/core";
import { ActivatedRoute, RouterOutlet } from "@angular/router";
import { NavbarComponent } from "../../components/navbar/navbar.component";
import { ProfileService } from "../../services/profile/profile.service";

@Component({
  selector: "app-main-layout",
  standalone: true,
  imports: [RouterOutlet, NavbarComponent],
  templateUrl: "./main-layout.component.html",
  styleUrl: "./main-layout.component.css",
})
export class MainLayoutComponent {}
