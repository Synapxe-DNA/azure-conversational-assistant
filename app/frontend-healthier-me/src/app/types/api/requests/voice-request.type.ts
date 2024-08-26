import { ApiChatHistory } from "../api-chat-history.type";
import { ApiProfile } from "../api-profile.type";

export interface ApiVoiceRequest {
  chat_history: ApiChatHistory[];
  profile: ApiProfile;
  query: Blob;
}
