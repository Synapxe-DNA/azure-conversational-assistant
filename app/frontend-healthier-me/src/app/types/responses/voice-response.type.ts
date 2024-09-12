import { ApiSource } from "../api/api-source.type";
import { ResponseStatus } from "./response-status.type";

export interface VoiceResponse {
  status: ResponseStatus;
  user_transcript: string;
  assistant_response: string;
  assistant_response_audio: string[];
  additional_questions: string[];
  sources: ApiSource[];
}
