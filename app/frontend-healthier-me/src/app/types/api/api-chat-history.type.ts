import { MessageSource } from "../message.type";

export interface ApiChatHistory {
  role: "assistant" | "user";
  content: string;
}

export interface ApiChatHistorywithSources {
  role: "assistant" | "user";
  content: string;
  sources: MessageSource[];
}
