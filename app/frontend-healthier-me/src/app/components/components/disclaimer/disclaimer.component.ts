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
    const isFirstLoad = sessionStorage.getItem("isFirstLoad");

    if (isFirstLoad === null) {
      console.log("First load detected, showing disclaimer.");
      this.showDisclaimer();
    } else {
      console.log("Disclaimer not shown, 'isFirstLoad' already set to: ", isFirstLoad);
    }
  }

  showDisclaimer() {
    this.isDisclaimerVisible = true;
    console.log("Showing disclaimer...");
  }

  closeDisclaimer() {
    this.isDisclaimerVisible = false;
    sessionStorage.setItem("isFirstLoad", "false");
    console.log("Disclaimer closed, 'isFirstLoad' set to false.");
  }
}
