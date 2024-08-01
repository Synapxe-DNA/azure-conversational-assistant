import { AfterViewInit, Injectable, OnInit } from "@angular/core"
import { NgxIndexedDBService } from "ngx-indexed-db"
import { Profile } from "../../types/profile.type"
import { BehaviorSubject } from "rxjs"
import {MessageService} from "primeng/api";
import {ActivatedRoute} from "@angular/router";

@Injectable({
  providedIn: "root",
})
export class ProfileService implements OnInit {
  $profiles: BehaviorSubject<Profile[]> = new BehaviorSubject<Profile[]>([])

  constructor(
    private dbService: NgxIndexedDBService,
    private route: ActivatedRoute
  ) {
    this.dbService.getAll<Profile>("profiles").subscribe((v) => {
      this.$profiles.next(v)
    })
  }

  ngOnInit() {}

  createProfile(profile: Profile) {
    this.dbService.add("profiles", { ...profile }).subscribe(() => {
      this.$profiles.next([...this.$profiles.value, profile])
    })
  }

  getProfiles(): BehaviorSubject<Profile[]> {
    return this.$profiles
  }

  getProfile(profileId:string):BehaviorSubject<Profile|undefined> {

    const returnProfile = new BehaviorSubject<Profile|undefined>(undefined)

    this.$profiles.subscribe(profiles => {
      const filtered = profiles.filter(p => p.id === profileId)

      if(filtered.length){
        returnProfile.next(filtered[0])
      }
    })


    return returnProfile

  }

  deleteProfile(id: string) {
    this.dbService.delete<Profile>("profiles", id).subscribe()
    this.$profiles.next(this.$profiles.value.filter((p) => p.id !== id))
  }
}
