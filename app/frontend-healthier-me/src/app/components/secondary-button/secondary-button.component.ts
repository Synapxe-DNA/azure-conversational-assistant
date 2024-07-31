import { Component, Input } from "@angular/core";
import { LucideAngularModule } from "lucide-angular";

@Component({
  selector: "app-secondary-button",
  standalone: true,
  imports: [LucideAngularModule],
  templateUrl: "./secondary-button.component.html",
  styleUrl: "./secondary-button.component.css",
})
export class SecondaryButtonComponent {
  @Input() type: "chat" | "profile" = "profile";

  get iconName(): string {
    return this.type === "chat" ? "message-square" : "user";
  }
}
