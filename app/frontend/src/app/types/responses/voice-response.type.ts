import { ApiSource } from "../api/api-source.type";
import { ResponseStatus } from "./response-status.type";

export interface VoiceResponse {
  status: ResponseStatus;
  assistant_response: string;
  assistant_response_audio: string[];
  sources: ApiSource[];
}
