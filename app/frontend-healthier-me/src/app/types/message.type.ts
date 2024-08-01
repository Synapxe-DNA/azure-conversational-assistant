export enum MessageRole {
  User = "USER",
  System = "SYSTEM",
}

export interface MessageSource {
  title: string
  description: string
  cover_image_url: string
  url: string
}

export interface Message {
  id: string
  profile_id: string
  role: MessageRole
  message: string
  timestamp: number
  sources?: MessageSource[]
}
