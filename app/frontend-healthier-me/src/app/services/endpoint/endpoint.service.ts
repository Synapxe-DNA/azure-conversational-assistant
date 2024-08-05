import { Injectable } from "@angular/core";
import { Observable, of } from "rxjs";

@Injectable({
  providedIn: "root",
})
export class EndpointService {
  constructor() {}

  textToSpeech(text: string): Observable<{ audio: string }> {
    const audioBase64 =
      "UklGRmACAABXQVZFZm10IBAAAAABAAEAgLsAAAB3AgAEABAAZGF0YQAQAAAAAIAcAAACABwAAIAcA" +
      "AICAAwBgAIAeAIAHgCAAHgIAABwDAACAAwAAIAcAAwAAAIAcAAcAAMAAAAgAwAAHAIAAB4AAIAcAA" +
      "AACAAwAAHgAAIAcAA4AAAACABwAAIAAAwAgAAHgAAIAAAQAA";
    console.log("EndpointService: textToSpeech()");
    return of({ audio: audioBase64 });
  }
}
