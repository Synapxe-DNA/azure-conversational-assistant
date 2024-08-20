export enum MessageRole {
  User = "USER",
  Assistant = "ASSISTANT",
}

export interface MessageSource {
  id: string;
  title: string;
  cover_image_url: string;
  full_url: string;
  content_category: string;
  chunks: string;
}

export interface Message {
  id: string;
  profile_id: string;
  role: MessageRole;
  message: string;
  timestamp: number;
  sources?: MessageSource[];
}
