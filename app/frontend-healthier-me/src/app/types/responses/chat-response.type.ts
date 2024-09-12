import { ResponseStatus } from "./response-status.type";
import { ApiSource } from "../api/api-source.type";

export interface ChatResponse {
  status: ResponseStatus;
  response: string;
  additional_questions: string[];
  sources: ApiSource[];
}
