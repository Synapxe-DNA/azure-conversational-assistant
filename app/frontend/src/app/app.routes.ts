import { Routes } from "@angular/router";
import { MainLayoutComponent } from "./layouts/main-layout/main-layout.component";
import { CreateProfileComponent } from "./pages/create-profile/create-profile.component";
import { EditProfileComponent } from "./pages/edit-profile/edit-profile.component";
import { ChatComponent } from "./pages/chat/chat.component";

export const routes: Routes = [
  {
    path: "",
    title: "HealthierME",
    component: MainLayoutComponent,
    children: [
      { path: "", pathMatch: "full", redirectTo: "/chat/general" },
      {
        path: "create",
        component: CreateProfileComponent
      },
      {
        path: "edit-profile/:profileId",
        component: EditProfileComponent
      },
      {
        path: "chat",
        children: [
          { path: "", pathMatch: "full", redirectTo: "/chat/general" },
          { path: "*", redirectTo: "/chat/general" },
          {
            path: ":profileId",
            component: ChatComponent
          }
        ]
      }
    ]
  },
  {
    path: "**",
    redirectTo: "/chat/general"
  }
];
