import {TestBed} from "@angular/core/testing"

import {PreferenceService} from "./preference.service"
import {PreferenceKey} from "../../types/configs/preference-keys.type";
import {ChatMode} from "../../types/chat-mode.type";

describe("PreferenceService", () => {
  let service: PreferenceService

  beforeEach(() => {
    TestBed.configureTestingModule({})
    service = TestBed.inject(PreferenceService)
  })

  it("should be created", () => {
    expect(service).toBeTruthy()
  })

  it("should initialise localStorage", ()=>{
    expect(JSON.parse(localStorage.getItem(PreferenceKey.ChatMode) as string)).toBe(service.$chatMode.value)
    expect(JSON.parse(localStorage.getItem(PreferenceKey.VoiceDetectInterrupt) as string)).toBe(service.$voiceDetectInterrupt.value)
    expect(JSON.parse(localStorage.getItem(PreferenceKey.VoiceDetectStart) as string)).toBe(service.$voiceDetectStart.value)
    expect(JSON.parse(localStorage.getItem(PreferenceKey.VoiceDetectEnd) as string)).toBe(service.$voiceDetectEnd.value)
  })

  it("should update $chatMode and localStorage", ()=>{
    // Sets starting point
    service.$chatMode.next(ChatMode.Voice)
    expect(service.$chatMode.value).toBe(ChatMode.Voice)
    expect(JSON.parse(localStorage.getItem(PreferenceKey.ChatMode) as string)).toBe(ChatMode.Voice)

    // Updates chat mode
    service.setChatMode(ChatMode.Text)
    expect(service.$chatMode.value).toBe(ChatMode.Text)
    expect(JSON.parse(localStorage.getItem(PreferenceKey.ChatMode) as string)).toBe(ChatMode.Text)
  })

  it("should update $voiceDetectInterrupt and localStorage", ()=>{
    // Sets starting point
    service.$voiceDetectInterrupt.next(false)
    expect(service.$voiceDetectInterrupt.value).toBe(false)
    expect(JSON.parse(localStorage.getItem(PreferenceKey.VoiceDetectInterrupt) as string)).toBe(false)

    // Updates voice interrupt
    service.setVoiceDetectInterrupt(true)
    expect(service.$voiceDetectInterrupt.value).toBe(true)
    expect(JSON.parse(localStorage.getItem(PreferenceKey.VoiceDetectInterrupt) as string)).toBe(true)
  })

  it("should update $voiceDetectStart and localStorage", ()=>{
    // Sets starting point
    service.$voiceDetectStart.next(false)
    expect(service.$voiceDetectStart.value).toBe(false)
    expect(JSON.parse(localStorage.getItem(PreferenceKey.VoiceDetectStart) as string)).toBe(false)

    // Updates voice start
    service.setVoiceDetectStart(true)
    expect(service.$voiceDetectStart.value).toBe(true)
    expect(JSON.parse(localStorage.getItem(PreferenceKey.VoiceDetectStart) as string)).toBe(true)
  })

  it("should update $voiceDetectEnd and localStorage", ()=>{
    // Sets starting point
    service.$voiceDetectEnd.next(false)
    expect(service.$voiceDetectEnd.value).toBe(false)
    expect(JSON.parse(localStorage.getItem(PreferenceKey.VoiceDetectEnd) as string)).toBe(false)

    // Updates voice end
    service.setVoiceDetectEnd(true)
    expect(service.$voiceDetectEnd.value).toBe(true)
    expect(JSON.parse(localStorage.getItem(PreferenceKey.VoiceDetectEnd) as string)).toBe(true)
  })
})
