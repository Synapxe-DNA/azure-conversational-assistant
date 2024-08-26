import { ApiSource } from "../api-source.type";

export interface ApiChatResponse {
    response_message: string;
    sources: ApiSource[];
    additional_question_1: string;
    additional_question_2: string;
}
