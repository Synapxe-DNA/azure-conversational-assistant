import { Component, OnInit, Input } from "@angular/core";
import { Button } from "primeng/button";
import { ConvoBrokerService } from "../../../services/convo-broker/convo-broker.service";
import { ProfileService } from "../../../services/profile/profile.service";
import { ActivatedRoute } from "@angular/router";
import { BehaviorSubject, takeWhile } from "rxjs";
import { GeneralProfile, Profile } from "../../../types/profile.type";
import { FollowUp } from "../../../types/follow-up.type";

@Component({
    selector: "app-text-followup",
    standalone: true,
    imports: [Button],
    templateUrl: "./text-followup.component.html",
    styleUrl: "./text-followup.component.css"
})
export class TextFollowupComponent implements OnInit {
    @Input() followUps?: FollowUp[];
    followUp1: string = "";
    followUp2: string = "";

    profile: BehaviorSubject<Profile | undefined> = new BehaviorSubject<Profile | undefined>(undefined);

    constructor(
        private convoBroker: ConvoBrokerService,
        private profileService: ProfileService,
        private route: ActivatedRoute
    ) {}

    ngOnInit(): void {
        this.route.paramMap
            .pipe(
                takeWhile(p => {
                    return p.get("profileId") !== undefined;
                }, true)
            )
            .subscribe(p => {
                this.profile = this.profileService.getProfile(p.get("profileId")!);
            });

        if (this.followUps) {
            this.followUp1 = this.followUps[-2].question;
            this.followUp2 = this.followUps[-1].question;
        }
    }

    sendFollowUp(message: string | undefined) {
        if (message) {
            this.convoBroker.sendChat(message, this.profile.value || GeneralProfile).catch(console.error);
        } else {
            console.log("Follow up is undefined");
        }
    }
}
