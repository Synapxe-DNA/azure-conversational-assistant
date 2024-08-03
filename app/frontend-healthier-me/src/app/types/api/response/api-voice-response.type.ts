export interface ApiVoiceResponse {
  response_message: string;
  query_message: string;
  sources: {
    title: string;
    url: string;
    meta_description: string;
    image_url: string;
  }[];
  additional_question_1: string;
  additional_question_2: string;
  audio_base64: string;
}
