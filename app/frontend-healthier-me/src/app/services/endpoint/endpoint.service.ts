import { Injectable } from "@angular/core";
import { Observable } from "rxjs";
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
import {
  ApiVoiceRequest,
  ApiVoiceRequest2,
} from "../../types/api/requests/voice-request.type";
import {
  ApiChatHistory,
  ApiChatHistorywithSources,
} from "../../types/api/api-chat-history.type";
import {
  ApiProfile,
  ApiProfileGender,
  ApiProfileType,
} from "../../types/api/api-profile.type";
import { ApiVoiceResponse } from "../../types/api/response/api-voice-response.type";
import { ApiSource } from "../../types/api/api-source.type";
import { ResponseStatus } from "../../types/responses/response-status.type";
import { ApiChatRequest } from "../../types/api/requests/chat-request.type";
import { createId } from "@paralleldrive/cuid2";
import { ApiChatResponse } from "../../types/api/response/api-chat-response.type";
import { Feedback } from "../../types/feedback.type";
import { ApiFeedbackRequest } from "../../types/api/requests/feedback-request.type";

@Injectable({
  providedIn: "root",
})
export class EndpointService {
  constructor(private httpClient: HttpClient) {}

  /**
   * Method to send previous system messages to backend for audio playback
   * @param text {string}
   */
  async textToSpeech(text: string): Promise<BehaviorSubject<Blob | null>> {
    const audioSubject = new BehaviorSubject<Blob | null>(null);

    try {
      const blob = await this.httpClient
        .post("/speech", { text }, { responseType: "blob" })
        .toPromise();

      if (blob instanceof Blob) {
        audioSubject.next(blob);
      } else {
        throw new Error("Unexpected response type");
      }
    } catch (error) {
      console.error("Error fetching audio:", error);
      audioSubject.error(error);
    }

    return audioSubject;
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
  private messageToApiChatHistoryWithSources(
    messages: Message[]
  ): ApiChatHistorywithSources[] {
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
        sources: m.sources,
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
    let currentQueryMessage: string = "";
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

              if (responseData.audio_base64) {
                existingAudio.push(responseData.audio_base64);
              }

              if (responseData.response_message) {
                currentAssistantMessage =
                  currentAssistantMessage + responseData.response_message;
              }

              if (responseData.query_message) {
                currentQueryMessage =
                  currentQueryMessage + responseData.query_message;
              }

              responseBS.next({
                status: ResponseStatus.Pending,
                user_transcript: currentQueryMessage,
                assistant_response: currentAssistantMessage,
                assistant_response_audio: existingAudio,
                additional_questions: [
                  responseData.additional_question_1,
                  responseData.additional_question_2,
                ],
                sources: responseData.sources,
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
   * Method to send transcribed text to the endpoint for LLM generation
   * @param message {string} transcribed text from websocket
   * @param profile {Profile}
   * @param history {Message[]} history of chat to be used for LLM context
   */
  async sendVoice2(
    message: string,
    profile: Profile,
    history: Message[]
  ): Promise<BehaviorSubject<VoiceResponse | null>> {
    const responseBS: BehaviorSubject<VoiceResponse | null> =
      new BehaviorSubject<VoiceResponse | null>(null);

    let lastResponseLength: number = 0;
    let currentAssistantMessage: string = "";
    let currentQueryMessage: string = "";
    let existingAudio: string[] = [];
    let currentSources: ApiSource[] = [];

    const data: ApiVoiceRequest2 = {
      chat_history: this.messageToApiChatHistory(history),
      profile: this.profileToApiProfile(profile),
      query: message,
    };

    this.httpClient
      .post("/voice", new TypedFormData<ApiVoiceRequest2>(data), {
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

              console.log("responseData", responseData);

              if (responseData.audio_base64) {
                existingAudio.push(responseData.audio_base64);
              }

              if (responseData.response_message) {
                currentAssistantMessage =
                  currentAssistantMessage + responseData.response_message;
              }

              if (responseData.query_message) {
                currentQueryMessage =
                  currentQueryMessage + responseData.query_message;
              }

              if (responseData.sources) {
                currentSources.push(...responseData.sources);
              }

              responseBS.next({
                status: ResponseStatus.Pending,
                user_transcript: currentQueryMessage,
                assistant_response: currentAssistantMessage,
                assistant_response_audio: existingAudio,
                additional_questions: [
                  responseData.additional_question_1,
                  responseData.additional_question_2,
                ],
                sources: currentSources,
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
    let currentResponseMessage: string = "";
    const currentSources: ApiSource[] = [];

    const data: ApiChatRequest = {
      chat_history: this.messageToApiChatHistory(history),
      profile: this.profileToApiProfile(profile),
      query: {
        role: "user",
        content: message.message,
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

              const currentResponseData = (
                e as HttpDownloadProgressEvent
              ).partialText!.slice(lastResponseLength); //splits response into chunks

              // console.log(currentResponseData)

              // parse chunks into multiple json objects

              const jsonParsed = this.parseSendChat(currentResponseData);

              //adds response_message to local variable
              currentResponseMessage += jsonParsed[0]; //currentResponseMessage should contain concated response
              currentSources.push(...jsonParsed[1]);

              responseBS.next({
                status: ResponseStatus.Pending,
                response: currentResponseMessage,
                additional_questions: [
                  // responseData.additional_question_1,
                  // responseData.additional_question_2,
                ],
                sources: currentSources,
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

  async sendFeedback(feedback: Feedback, profile: Profile): Promise<void> {
    const data: ApiFeedbackRequest = {
      date_time: feedback.datetime,
      feedback_type: feedback.label,
      feedback_category: feedback.category,
      feedback_remarks: feedback.remarks,
      user_profile: this.profileToApiProfile(profile),
      chat_history: this.messageToApiChatHistoryWithSources(
        feedback.chat_history
      ),
    };

    this.httpClient.post("/feedback", data);
  }

  // Function to extract individual JSON objects from a concatenated raw JSON string
  private extractJsonObjects(rawString: string): string[] {
    // Regular expression to match JSON objects
    const jsonObjects: string[] = [];
    const jsonRegex = /\{.*?\}(?=\{|\s*$)/g; // Regex to capture non-nested JSON objects
    let match;

    // Find all matches
    while ((match = jsonRegex.exec(rawString)) !== null) {
      jsonObjects.push(match[0]);
    }
    // console.log(jsonObjects)

    return jsonObjects;
  }

  // Function to aggregate response messages from concatenated JSON objects
  private parseSendChat(rawJsonString: string): any[] {
    let aggregatedResponseMessage: string = "";
    let aggregatedSources: [] = [];

    // Extract individual JSON objects
    const jsonObjects = this.extractJsonObjects(rawJsonString);

    // Process each JSON object
    for (const jsonObject of jsonObjects) {
      try {
        // Parse the JSON object
        const data = JSON.parse(jsonObject);

        // Extract and append the response message
        const responseMessage: string = data.response_message || "";
        const sources: [] = data.sources || [];
        aggregatedResponseMessage += responseMessage;
        aggregatedSources.push(...sources);
      } catch (error) {
        console.error("Error decoding JSON:", error);
      }
    }
    return [aggregatedResponseMessage, aggregatedSources];
  }
}
