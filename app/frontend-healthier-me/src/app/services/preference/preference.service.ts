import {Injectable, OnInit} from "@angular/core"
import { BehaviorSubject } from "rxjs"
import { ChatMode } from "../../types/chat-mode.type"
import {PreferenceKey} from "../../types/configs/preference-keys.type";

@Injectable({
  providedIn: "root",
})
export class PreferenceService{
  /**
   * This service is used to set the user preference across the webapp.
   */

  // BehaviorSubject to manage chat mode state
  $chatMode = new BehaviorSubject<ChatMode>(this.loadFromLocalStorage<ChatMode>(PreferenceKey.ChatMode, ChatMode.Voice))

  // BehaviorSubjects to manage voice detection states
  $voiceDetectInterrupt = new BehaviorSubject<boolean>(this.loadFromLocalStorage<boolean>(PreferenceKey.VoiceDetectInterrupt, false))
  $voiceDetectStart = new BehaviorSubject<boolean>(this.loadFromLocalStorage<boolean>(PreferenceKey.VoiceDetectStart, false))
  $voiceDetectEnd = new BehaviorSubject<boolean>(this.loadFromLocalStorage<boolean>(PreferenceKey.VoiceDetectEnd, false))

  constructor() {
    this.initialisePreferences()
    this.listenToLocalStorageEvents()
  }

  /**
   * Initialize preferences by subscribing to BehaviorSubjects and updating local storage accordingly
   * @private
   */
  private initialisePreferences(){
    this.$chatMode.subscribe(v => {this.setToLocalStorage<ChatMode>(PreferenceKey.ChatMode, v)})
    this.$voiceDetectInterrupt.subscribe(v => {this.setToLocalStorage<boolean>(PreferenceKey.VoiceDetectInterrupt, v)})
    this.$voiceDetectStart.subscribe(v => {this.setToLocalStorage<boolean>(PreferenceKey.VoiceDetectStart, v)})
    this.$voiceDetectEnd.subscribe(v => {this.setToLocalStorage<boolean>(PreferenceKey.VoiceDetectEnd, v)})
  }

  /**
   * Listen to local storage events and update BehaviorSubjects if relevant keys are modified
   * @private
   */
  private listenToLocalStorageEvents(){
    const updateStates = (e:StorageEvent) => {

      if(!e.key || !Object.values(PreferenceKey).includes(e.key as PreferenceKey)){
        // DON'T DO ANYTHING IF:
        // - Local storage has been cleared
        // - Affected storage key is not our preference key
        return
      }

      switch (e.key){
        case PreferenceKey.ChatMode: {
          this.$chatMode.next(this.loadFromLocalStorage(PreferenceKey.ChatMode, ChatMode.Voice))
          break
        }
        case PreferenceKey.VoiceDetectInterrupt: {
          this.$voiceDetectInterrupt.next(this.loadFromLocalStorage(PreferenceKey.VoiceDetectInterrupt, false))
          break
        }
        case PreferenceKey.VoiceDetectStart: {
          this.$voiceDetectStart.next(this.loadFromLocalStorage(PreferenceKey.VoiceDetectStart, false))
          break
        }
        case PreferenceKey.VoiceDetectEnd: {
          this.$voiceDetectEnd.next(this.loadFromLocalStorage(PreferenceKey.VoiceDetectEnd, false))
          break
        }

      }
    }

    window.addEventListener("storage", (e:StorageEvent)=>{updateStates(e)})
  }

  /**
   * Load a value from local storage or use the default value if not present
   * @template T
   * @param key {PreferenceKey} key used to store preference
   * @param defaultValue {T} value to be used if local storage value is not set, or if jey does not exist
   * @private
   */
  private loadFromLocalStorage<T>(key:PreferenceKey, defaultValue:T):T{
    const storedValue = localStorage.getItem(key)
    if(storedValue){
      return JSON.parse(storedValue) as T
    }

    this.setToLocalStorage(key, defaultValue)
    return defaultValue
  }

  /**
   * Sets a value in local storage.
   * @template T
   * @param {string} key - The key under which to store the value.
   * @param {T} value - The value to store.
   */
  private setToLocalStorage<T>(key: string, value: T): void {
    localStorage.setItem(key, JSON.stringify(value))
  }

  /**
   * Sets the chat mode.
   * @param {ChatMode} mode - The chat mode to set.
   */
  setChatMode(mode: ChatMode): void {
    this.$chatMode.next(mode)
  }

  /**
   * Sets whether voice detection should interrupt.
   * @param {boolean} value - True if voice detection should interrupt, false otherwise.
   */
  setVoiceDetectInterrupt(value: boolean): void {
    this.$voiceDetectInterrupt.next(value)
  }

  /**
   * Sets whether voice detection should start.
   * @param {boolean} value - True if voice detection should start, false otherwise.
   */
  setVoiceDetectStart(value: boolean): void {
    this.$voiceDetectStart.next(value)
  }

  /**
   * Sets whether voice detection should end.
   * @param {boolean} value - True if voice detection should end, false otherwise.
   */
  setVoiceDetectEnd(value: boolean): void {
    this.$voiceDetectEnd.next(value)
  }


}
