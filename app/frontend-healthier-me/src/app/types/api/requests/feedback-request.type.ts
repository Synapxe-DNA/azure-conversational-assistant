import { ApiChatHistory } from "../api-chat-history.type";
import { ApiProfile } from "../api-profile.type";

export interface ApiFeedbackRequest {
  chatHistory: ApiChatHistory[];
  label: string;
  category: string;
  remarks: string;
  userProfile: ApiProfile;
  retrievedSources: string;
  userId: string;
}
