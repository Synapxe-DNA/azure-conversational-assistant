import { ResponseStatus } from "./response-status.type";
import { Message } from "../message.type";

export interface ChatResponse {
  status: ResponseStatus;
  response: Message;
  additional_questions: string[];
}
