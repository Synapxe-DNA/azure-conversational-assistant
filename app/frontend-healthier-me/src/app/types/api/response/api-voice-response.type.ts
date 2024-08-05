import { ApiSource } from "../api-source.type";

export interface ApiVoiceResponse {
  response_message: string;
  query_message: string;
  sources: ApiSource[];
  additional_question_1: string;
  additional_question_2: string;
  audio_base64: string;
}
