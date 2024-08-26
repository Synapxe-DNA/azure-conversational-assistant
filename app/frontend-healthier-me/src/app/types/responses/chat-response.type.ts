import { ResponseStatus } from "./response-status.type";
import { Message } from "../message.type";

export interface ChatResponse {
    status: ResponseStatus;
    response: string;
    additional_questions: string[];
}
