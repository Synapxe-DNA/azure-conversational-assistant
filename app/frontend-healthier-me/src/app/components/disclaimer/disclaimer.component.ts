import { Component, OnInit } from "@angular/core";
import { DialogModule } from "primeng/dialog";
import { CommonModule } from "@angular/common";

@Component({
  selector: "app-disclaimer",
  standalone: true,
  imports: [CommonModule, DialogModule],
  templateUrl: "./disclaimer.component.html",
  styleUrls: ["./disclaimer.component.css"]
})
export class DisclaimerComponent implements OnInit {
  isDisclaimerVisible: boolean = false;

  ngOnInit(): void {
    this.checkDisclaimerStatus();
  }

  checkDisclaimerStatus() {
    const readDisclaimer = sessionStorage.getItem("readDisclaimer");

    if (!readDisclaimer) {
      this.showDisclaimer();
    }
  }

  showDisclaimer() {
    this.isDisclaimerVisible = true;
  }

  closeDisclaimer() {
    this.isDisclaimerVisible = false;
    sessionStorage.setItem("readDisclaimer", "true");
  }
}
