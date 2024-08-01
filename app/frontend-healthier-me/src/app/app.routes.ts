import { Routes } from "@angular/router"
import { MainLayoutComponent } from "./layouts/main-layout/main-layout.component"
import { CreateProfileComponent } from "./pages/create-profile/create-profile.component"
import { ChatComponent } from "./pages/chat/chat.component"

export const routes: Routes = [
  {
    path: "",
    component: MainLayoutComponent,
    children: [
      {path: "", pathMatch:"full", redirectTo:"/chat/general"},
      {
        path: "create",
        component: CreateProfileComponent,
      },

      {
        path: "chat",
        children: [
          { path: "", pathMatch: "full", redirectTo: "/chat/general" },
          { path: "*", redirectTo: "/chat/general" },
          {
            path: ":profileId",
            component: ChatComponent,
          },
        ],
      },
    ],
  },
  {
    path: "**",
    redirectTo: "/chat/general",
  },
]
