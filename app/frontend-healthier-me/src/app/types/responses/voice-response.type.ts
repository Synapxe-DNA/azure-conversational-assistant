import { Message } from "../message.type";
import { ResponseStatus } from "./response-status.type";

export interface VoiceResponse {
  status: ResponseStatus;
  user_transcript: Message;
  system_response: Message;
  system_response_audio: Blob;
  additional_questions: string[];
}
