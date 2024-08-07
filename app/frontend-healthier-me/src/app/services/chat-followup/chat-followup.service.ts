import { Injectable } from '@angular/core';
import { NgxIndexedDBService } from 'ngx-indexed-db';
import { BehaviorSubject, firstValueFrom } from 'rxjs';
import { FollowUp } from '../../types/follow-up.type';


@Injectable({
  providedIn: 'root'
})
export class ChatFollowupService {
  private $followUp: BehaviorSubject<FollowUp[]> = new BehaviorSubject<FollowUp[]>([]);
  private $currentProfileId: BehaviorSubject<string> = new BehaviorSubject("");

  constructor(private indexedStore: NgxIndexedDBService) { }

  async load(profileId: string): Promise<BehaviorSubject<FollowUp[]>> {
    this.$currentProfileId.next(profileId);

    const followUps = await firstValueFrom<FollowUp[] | undefined>(
      this.indexedStore.getAllByIndex(
        "follow_up",
        "profile_id",
        IDBKeyRange.only(profileId),
      ),
    );
    this.$followUp = new BehaviorSubject<FollowUp[]>(
      followUps || []
    );

    return this.$followUp;
  }

  async staticLoad(profileId: string): Promise<FollowUp[]> {
    return await firstValueFrom<FollowUp[]>(
      this.indexedStore.getAllByIndex(
        "follow_up",
        "profile_id",
        IDBKeyRange.only(profileId),
      ),
    );
  }

  insert(followUp: FollowUp): Promise<void> {
    if (followUp.profile_id !== this.$currentProfileId.value) {
      console.warn(
        "[FollowupService] Attempting to insert question that does not match current profile ID!",
      );
    }

    return new Promise((resolve) => {
      this.indexedStore.add("follow_up", followUp).subscribe({
        next: () => {
          this.$followUp.next([...this.$followUp.value, followUp]);
          resolve();
        },
        error: console.error,
      });
    });
  }

  upsert(followup: FollowUp): Promise<void> {
    // Checks if follow_up is in current memory
    const index = this.$followUp.value.findIndex((f) => f.id === followup.id);

    // If message exists
    if (index >= 0) {
      return new Promise((resolve) => {
        this.indexedStore.update<FollowUp>("follow_up", followup).subscribe({
          next: () => {
            let arr = this.$followUp.value;
            arr[index] = followup;
            this.$followUp.next(arr);
            resolve();
          },
        });
      });
    }

    return this.insert(followup);
  }

}
