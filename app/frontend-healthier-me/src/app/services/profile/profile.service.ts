import { AfterViewInit, Injectable, OnInit } from "@angular/core";
import { NgxIndexedDBService } from "ngx-indexed-db";
import { GeneralProfile, Profile } from "../../types/profile.type";
import { BehaviorSubject } from "rxjs";
import { MessageService } from "primeng/api";
import { ActivatedRoute } from "@angular/router";

@Injectable({
    providedIn: "root"
})
export class ProfileService {
    $profiles: BehaviorSubject<Profile[]> = new BehaviorSubject<Profile[]>([]);
    $currentProfileInUrl: BehaviorSubject<string> = new BehaviorSubject<string>("");

    constructor(
        private dbService: NgxIndexedDBService,
        private route: ActivatedRoute
    ) {
        this.dbService.getAll<Profile>("profiles").subscribe(v => {
            this.$profiles.next(v);
        });
    }

    setProfileInUrl(id: string) {
        this.$currentProfileInUrl.next(id);
    }

    /**
     * Method to persist a profile
     * @param profile {profile}
     */
    createProfile(profile: Profile) {
        this.dbService.add("profiles", { ...profile }).subscribe(() => {
            this.$profiles.next([...this.$profiles.value, profile]);
        });
    }

    /**
     * Method to return all existing profiles
     */
    getProfiles(): BehaviorSubject<Profile[]> {
        return this.$profiles;
    }

    /**
     * Method to get a specific profile by ID
     * @param profileId {string}
     */
    getProfile(profileId: string): BehaviorSubject<Profile | undefined> {
        const returnProfile = new BehaviorSubject<Profile | undefined>(undefined);

        this.$profiles.subscribe(profiles => {
            const filtered = profiles.filter(p => p.id === profileId);

            if (filtered.length) {
                returnProfile.next(filtered[0]);
            }

            if (profileId === GeneralProfile.id) {
                returnProfile.next(GeneralProfile);
            }
        });

        return returnProfile;
    }

    /**
     * Method to delete a profile by ID
     * @param id {string}
     */
    deleteProfile(id: string) {
        this.dbService.delete<Profile>("profiles", id).subscribe();
        this.$profiles.next(this.$profiles.value.filter(p => p.id !== id));
    }
}
