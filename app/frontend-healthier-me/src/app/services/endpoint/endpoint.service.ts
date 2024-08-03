import { Injectable } from "@angular/core";
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

@Injectable({
  providedIn: "root",
})
export class EndpointService {
  constructor(private httpClient: HttpClient) {}

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
        message: m.message,
      };
    });
  }

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
      user_age: profile.age,
      user_condition: profile.existing_conditions,
      user_gender: profileGender(),
    };
  }

  async sendVoice(
    recording: Blob,
    profile: Profile,
    history: Message[],
  ): Promise<BehaviorSubject<VoiceResponse | null>> {
    const responseBS: BehaviorSubject<VoiceResponse | null> =
      new BehaviorSubject<VoiceResponse | null>(null);

    let lastResponseLength: number = 0;

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
                  lastResponseLength,
                ),
              ) as ApiVoiceResponse;
              responseBS.next({
                status: ResponseStatus.Pending,
                user_transcript: responseData.query_message,
                assistant_response: responseData.response_message,
                assistant_response_audio: responseData.audio_base64,
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

  async sendChat(
    message: Message,
    profile: Profile,
    history: Message[],
  ): Promise<BehaviorSubject<ChatResponse>> {
    return undefined as unknown as BehaviorSubject<ChatResponse>;
  }
}
