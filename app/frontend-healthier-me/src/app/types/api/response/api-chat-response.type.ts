import { ApiSource } from "../api-source.type";

export interface ApiChatResponse {
  message: string;
  sources: ApiSource[];
  additional_question_1: string;
  additional_question_2: string;
}
