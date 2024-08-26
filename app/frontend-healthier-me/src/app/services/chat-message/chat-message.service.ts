import { Injectable } from "@angular/core";
import { NgxIndexedDBService } from "ngx-indexed-db";
import { BehaviorSubject, firstValueFrom } from "rxjs";
import { Message } from "../../types/message.type";

@Injectable({
  providedIn: "root"
})
export class ChatMessageService {
  private $messages: BehaviorSubject<Message[]> = new BehaviorSubject<Message[]>([]);
  private $currentProfileId: BehaviorSubject<string> = new BehaviorSubject("");

  constructor(private indexedStore: NgxIndexedDBService) {}

  /**
   * Method to load existing messages into a behavior state (aka "memory").
   * @param profileId {string} ID of the profile stored in memory.
   * @return {BehaviorSubject<Message[]>} BS tracking the messages.
   *
   * NOTE! Upon calling ChatMessageService.load(), the private $messages is re-initialised, so if for whatever reason
   * when the private $messages get updated, the returned BS (from earlier method calls) will still contain the messages,
   * just that it won't be updated.
   */
  async load(profileId: string): Promise<BehaviorSubject<Message[]>> {
    this.$currentProfileId.next(profileId);

    const messages = await firstValueFrom<Message[] | undefined>(this.indexedStore.getAllByIndex("messages", "profile_id", IDBKeyRange.only(profileId)));
    this.$messages = new BehaviorSubject<Message[]>(messages?.sort((a, b) => a.timestamp - b.timestamp) || []);

    return this.$messages;
  }

  async staticLoad(profileId: string): Promise<Message[]> {
    const messages = await firstValueFrom<Message[]>(this.indexedStore.getAllByIndex("messages", "profile_id", IDBKeyRange.only(profileId)));
    return messages?.sort((a, b) => a.timestamp - b.timestamp) || [];
  }

  /**
   * Method to insert message into indexed store, and update local behavior subject
   * @param message
   */
  insert(message: Message): Promise<void> {
    if (message.profile_id !== this.$currentProfileId.value) {
      console.warn("[ChatMessageService] Attempting to insert message that does not match current profile ID!");
    }

    return new Promise(resolve => {
      this.indexedStore.add("messages", message).subscribe({
        next: () => {
          this.$messages.next([...this.$messages.value, message]);
          resolve();
        },
        error: console.error
      });
    });
  }

  /**
   * Method to update a message in memory and in the store. This method will create a new message if it does not exist.
   * @param message
   */
  upsert(message: Message): Promise<void> {
    // Checks if message is in current memory
    const index = this.$messages.value.findIndex(m => m.id === message.id);

    // If message exists
    if (index >= 0) {
      return new Promise(resolve => {
        this.indexedStore.update<Message>("messages", message).subscribe({
          next: () => {
            let arr = this.$messages.value;
            arr[index] = message;
            this.$messages.next(arr);
            resolve();
          }
        });
      });
    }

    return this.insert(message);
  }
}
