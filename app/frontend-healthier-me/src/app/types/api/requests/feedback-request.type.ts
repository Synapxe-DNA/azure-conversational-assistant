import { ApiChatHistorywithSources } from "../api-chat-history.type";
import { ApiProfile } from "../api-profile.type";

export interface ApiFeedbackRequest {
  date_time: string;
  feedback_type: string;
  feedback_category: string;
  feedback_remarks: string;
  user_profile: ApiProfile;
  chat_history: ApiChatHistorywithSources[];
}
