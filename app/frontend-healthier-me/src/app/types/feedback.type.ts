import { Message, MessageSource } from "./message.type";
import { Profile } from "./profile.type";

export interface Feedback {
  label: string;
  category: string;
  remarks: string;
  chat_history: Message[];
  profile_id: string;
  datetime: string;
}
