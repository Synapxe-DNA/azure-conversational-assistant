import { ApiChatHistory } from "../api-chat-history.type";
import { ApiProfile } from "../api-profile.type";

export interface ApiChatRequest {
    chat_history: ApiChatHistory[];
    profile: ApiProfile;
    query: {
        role: "user";
        content: string;
    };
}
