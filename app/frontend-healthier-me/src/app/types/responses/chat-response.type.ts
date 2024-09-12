import { ResponseStatus } from "./response-status.type";
import { ApiSource } from "../api/api-source.type";

export interface ChatResponse {
  status: ResponseStatus;
  response: string;
  sources: ApiSource[];
}
