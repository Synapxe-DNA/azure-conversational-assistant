import { ApiChatHistory } from "../api-chat-history.type";
import { ApiProfile } from "../api-profile.type";

export interface ApiVoiceRequest {
  chat_history: ApiChatHistory[];
  profile: ApiProfile;
  query: Blob;
}

export interface ApiVoiceRequest2 {
  chat_history: ApiChatHistory[];
  profile: ApiProfile;
  query: {
    role: "user";
    content: string;
  };
  language: string;
}
