import { Component } from "@angular/core";
import { ProgressSpinnerModule } from "primeng/progressspinner";

@Component({
  selector: "app-text-loading",
  standalone: true,
  imports: [ProgressSpinnerModule],
  templateUrl: "./text-loading.component.html",
  styleUrl: "./text-loading.component.css"
})
export class TextLoadingComponent {}
