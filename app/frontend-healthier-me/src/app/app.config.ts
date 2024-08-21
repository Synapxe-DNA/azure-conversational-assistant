import {
  ApplicationConfig,
  importProvidersFrom,
  provideZoneChangeDetection,
  isDevMode,
} from "@angular/core";
import { provideRouter } from "@angular/router";

import { routes } from "./app.routes";
import { BrowserModule } from "@angular/platform-browser";
import { BrowserAnimationsModule } from "@angular/platform-browser/animations";
import { NgxIndexedDBModule } from "ngx-indexed-db";
import { NgxIndexedDbConfig } from "./configs/ngx-indexed-db/ngx-indexed-db.config";
import {
  LucideAngularModule,
  MessageSquare,
  Mic,
  MicOff,
  Settings,
  User,
  UserRoundPlus,
  Send,
  StopCircle,
  Copy,
} from "lucide-angular";
import { ToastModule } from "primeng/toast";
import { provideHttpClient, withFetch } from "@angular/common/http";
import { provideServiceWorker } from "@angular/service-worker";
import { provideMarkdown } from "ngx-markdown";

export const appConfig: ApplicationConfig = {
  providers: [
    provideMarkdown(),
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    importProvidersFrom(BrowserModule),
    importProvidersFrom(BrowserAnimationsModule),
    provideHttpClient(withFetch()),
    importProvidersFrom(NgxIndexedDBModule.forRoot(NgxIndexedDbConfig)),
    importProvidersFrom(
      LucideAngularModule.pick({
        UserRoundPlus,
        Mic,
        MicOff,
        MessageSquare,
        User,
        Settings,
        Send,
        StopCircle,
        Copy,
      })
    ),
    importProvidersFrom(ToastModule),
    provideServiceWorker("ngsw-worker.js", {
      enabled: !isDevMode(),
      registrationStrategy: "registerWhenStable:30000",
    }),
    provideServiceWorker("ngsw-worker.js", {
      enabled: !isDevMode(),
      registrationStrategy: "registerWhenStable:30000",
    }),
  ],
};
