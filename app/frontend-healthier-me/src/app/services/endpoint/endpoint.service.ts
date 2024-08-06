import { Injectable } from "@angular/core";
import { map } from "rxjs";
import { Profile, ProfileGender, ProfileType } from "../../types/profile.type";
import { BehaviorSubject } from "rxjs";
import { VoiceResponse } from "../../types/responses/voice-response.type";
import { Message, MessageRole } from "../../types/message.type";
import { ChatResponse } from "../../types/responses/chat-response.type";
import {
  HttpClient,
  HttpDownloadProgressEvent,
  HttpEventType,
} from "@angular/common/http";
import { TypedFormData } from "../../utils/typed-form-data";
import { ApiVoiceRequest } from "../../types/api/requests/voice-request.type";
import { ApiChatHistory } from "../../types/api/api-chat-history.type";
import {
  ApiProfile,
  ApiProfileGender,
  ApiProfileType,
} from "../../types/api/api-profile.type";
import { ApiVoiceResponse } from "../../types/api/response/api-voice-response.type";
import { ResponseStatus } from "../../types/responses/response-status.type";
import { ApiChatRequest } from "../../types/api/requests/chat-request.type";
import { createId } from "@paralleldrive/cuid2";
import { ApiChatResponse } from "../../types/api/response/api-chat-response.type";

@Injectable({
  providedIn: "root",
})
export class EndpointService {
  constructor(private httpClient: HttpClient) {}

  async textToSpeech(
    text: string
  ): Promise<BehaviorSubject<{ audio: string } | null>> {
    const responseBS = new BehaviorSubject<{ audio: string } | null>(null);

    this.httpClient
      .post<{ audio: string }>("/tts", { text })
      .pipe(
        map((response) => {
          return { audio: response.audio };
        })
      )
      .subscribe({
        next: (audioData) => {
          responseBS.next(audioData);
          responseBS.complete();
        },
        error: (error) => {
          console.error(error);
          responseBS.error(error);
        },
      });

    return responseBS;
  }

  /**
   * Method to convert messages (frontend format) to format suitable for backend consumption
   * @param messages {Message[]}
   * @return {ApiChatHistory[]}
   * @private
   */
  private messageToApiChatHistory(messages: Message[]): ApiChatHistory[] {
    return messages.map((m) => {
      const role = () => {
        switch (m.role) {
          case MessageRole.User:
            return "user";
          case MessageRole.Assistant:
            return "assistant";
        }
      };

      return {
        role: role(),
        content: m.message,
      };
    });
  }

  /**
   * Method to convert profile (frontend format) to format suitable for backend consumption
   * @param profile {Profile}
   * @return {ApiProfile}
   * @private
   */
  private profileToApiProfile(profile: Profile): ApiProfile {
    const profileType = () => {
      switch (profile.profile_type) {
        case ProfileType.Myself:
          return ApiProfileType.Myself;
        case ProfileType.Others:
          return ApiProfileType.Others;
        default:
          return ApiProfileType.General;
      }
    };

    const profileGender = () => {
      switch (profile.gender) {
        case ProfileGender.Male:
          return ApiProfileGender.Male;
        case ProfileGender.Female:
          return ApiProfileGender.Female;
        default:
          return ApiProfileGender.Male; // can't spell female without male
      }
    };

    return {
      profile_type: profileType(),
      user_age: profile.age || -1,
      user_condition: profile.existing_conditions,
      user_gender: profileGender(),
    };
  }

  /**
   * Method to send voice blob to the endpoint for LLM generation
   * @param recording {Blob} Audio file with user recording
   * @param profile {Profile}
   * @param history {Message[]} history of chat to be used for LLM context
   */
  async sendVoice(
    recording: Blob,
    profile: Profile,
    history: Message[]
  ): Promise<BehaviorSubject<VoiceResponse | null>> {
    const responseBS: BehaviorSubject<VoiceResponse | null> =
      new BehaviorSubject<VoiceResponse | null>(null);

    let lastResponseLength: number = 0;
    let currentAssistantMessage: string = "";
    let existingAudio: string[] = [];

    const data: ApiVoiceRequest = {
      chat_history: this.messageToApiChatHistory(history),
      profile: this.profileToApiProfile(profile),
      query: recording,
    };

    this.httpClient
      .post("/voice", new TypedFormData<ApiVoiceRequest>(data), {
        responseType: "text",
        reportProgress: true,
        observe: "events",
      })
      .subscribe({
        next: (e) => {
          switch (e.type) {
            case HttpEventType.DownloadProgress: {
              if (!(e as HttpDownloadProgressEvent).partialText) {
                return;
              }
              const responseData = JSON.parse(
                (e as HttpDownloadProgressEvent).partialText!.slice(
                  lastResponseLength
                )
              ) as ApiVoiceResponse;

              console.log(
                (e as HttpDownloadProgressEvent).partialText!.slice(
                  lastResponseLength
                )
              );

              if (responseData.audio_base64) {
                existingAudio.push(responseData.audio_base64);
              }

              if (responseData.response_message) {
                currentAssistantMessage =
                  currentAssistantMessage + responseData.response_message;
              }

              responseBS.next({
                status: ResponseStatus.Pending,
                user_transcript: responseData.query_message,
                assistant_response: currentAssistantMessage,
                assistant_response_audio: existingAudio,
                additional_questions: [
                  responseData.additional_question_1,
                  responseData.additional_question_2,
                ],
              });
              lastResponseLength =
                (e as HttpDownloadProgressEvent).partialText?.length || 0;
              return;
            }
            case HttpEventType.Response: {
              let existingData = responseBS.value!;
              existingData.status = ResponseStatus.Done;
              responseBS.next(existingData);
              return;
            }
          }
        },
        error: console.error,
      });

    return responseBS;
  }

  /**
   * Method to send chat message to LLM for generation
   * @param message {Message} user message
   * @param profile {Profile}
   * @param history {Message[]} history of conversation for LLM context
   */
  async sendChat(
    message: Message,
    profile: Profile,
    history: Message[]
  ): Promise<BehaviorSubject<ChatResponse | null>> {
    const responseBS: BehaviorSubject<ChatResponse | null> =
      new BehaviorSubject<ChatResponse | null>(null);
    const responseId = createId();

    let lastResponseLength: number = 0;

    const data: ApiChatRequest = {
      chat_history: this.messageToApiChatHistory(history),
      profile: this.profileToApiProfile(profile),
      query: {
        role: "user",
        message: message.message,
      },
    };

    this.httpClient
      .post("/chat/stream", new TypedFormData<ApiChatRequest>(data), {
        responseType: "text",
        reportProgress: true,
        observe: "events",
      })
      .subscribe({
        next: (e) => {
          switch (e.type) {
            case HttpEventType.DownloadProgress: {
              if (!(e as HttpDownloadProgressEvent).partialText) {
                return;
              }

              const responseData = JSON.parse(
                (e as HttpDownloadProgressEvent).partialText!.slice(
                  lastResponseLength
                )
              ) as ApiChatResponse;

              responseBS.next({
                status: ResponseStatus.Pending,
                response: responseData.message,
                additional_questions: [
                  responseData.additional_question_1,
                  responseData.additional_question_2,
                ],
              });

              lastResponseLength =
                (e as HttpDownloadProgressEvent).partialText?.length || 0;
              break;
            }

            case HttpEventType.Response: {
              let latestData = responseBS.value;
              latestData!.status = ResponseStatus.Done;
              responseBS.next(latestData);
              break;
            }
          }
        },
        error: console.error,
      });

    return responseBS;
  }
}
