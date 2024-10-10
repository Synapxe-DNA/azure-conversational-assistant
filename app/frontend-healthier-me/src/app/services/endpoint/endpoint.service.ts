import { Injectable } from "@angular/core";
import { Observable, Subscription } from "rxjs";
import { Profile, ProfileGender, ProfileType } from "../../types/profile.type";
import { BehaviorSubject } from "rxjs";
import { VoiceResponse } from "../../types/responses/voice-response.type";
import { Message, MessageRole } from "../../types/message.type";
import { ChatResponse } from "../../types/responses/chat-response.type";
import { HttpClient, HttpDownloadProgressEvent, HttpEventType } from "@angular/common/http";
import { TypedFormData } from "../../utils/typed-form-data";
import { ApiVoiceRequest, ApiVoiceRequest2 } from "../../types/api/requests/voice-request.type";
import { ApiChatHistory, ApiChatHistorywithSources } from "../../types/api/api-chat-history.type";
import { ApiProfile, ApiProfileGender, ApiProfileType } from "../../types/api/api-profile.type";
import { ApiVoiceResponse } from "../../types/api/response/api-voice-response.type";
import { ApiSource } from "../../types/api/api-source.type";
import { ResponseStatus } from "../../types/responses/response-status.type";
import { ApiChatRequest } from "../../types/api/requests/chat-request.type";
import { createId } from "@paralleldrive/cuid2";
import { ApiChatResponse } from "../../types/api/response/api-chat-response.type";
import { Feedback } from "../../types/feedback.type";
import { ApiFeedbackRequest } from "../../types/api/requests/feedback-request.type";
import { APP_CONSTANTS } from "../../constants";
@Injectable({
  providedIn: "root"
})
export class EndpointService {
  private voiceSubscription: Subscription | null = null;

  constructor(private httpClient: HttpClient) {}

  /**
   * Method to send previous system messages to backend for audio playback
   * @param text {string}
   */
  async textToSpeech(text: string): Promise<BehaviorSubject<Blob | null>> {
    const audioSubject = new BehaviorSubject<Blob | null>(null);

    try {
      const blob = await this.httpClient.post("/speech", { text }, { responseType: "blob" }).toPromise();

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
    return messages.map(m => {
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
        content: m.message
      };
    });
  }

  private messageToApiChatHistoryWithSources(messages: Message[]): ApiChatHistorywithSources[] {
    return messages.map(m => {
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
        sources: m.sources
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
      user_gender: profileGender()
    };
  }

  /**
   * Method to send transcribed text to the endpoint for LLM generation
   * @param message {string} transcribed text from websocket
   * @param profile {Profile}
   * @param history {Message[]} history of chat to be used for LLM context
   */
  async sendVoice(message: string, profile: Profile, history: Message[], language: string): Promise<BehaviorSubject<VoiceResponse | null>> {
    const responseBS: BehaviorSubject<VoiceResponse | null> = new BehaviorSubject<VoiceResponse | null>(null);

    let lastResponseLength: number = 0;
    let currentAssistantMessage: string = "";
    const existingAudio: string[] = [];
    const currentSources: ApiSource[] = [];

    const data: ApiVoiceRequest2 = {
      chat_history: this.messageToApiChatHistory(history),
      profile: this.profileToApiProfile(profile),
      query: {
        role: "user",
        content: message
      },
      language: language.toLowerCase()
    };

    // Timeout setup
    const timeout = setTimeout(() => {
      console.log("Timed Out");
      responseBS.next({
        status: ResponseStatus.Timeout,
        assistant_response: currentAssistantMessage,
        assistant_response_audio: existingAudio,
        sources: currentSources
      });
      this.voiceSubscription?.unsubscribe(); // Unsubscribe from the HTTP request
    }, APP_CONSTANTS.VOICE_TIMEOUT);

    this.voiceSubscription = this.httpClient
      .post("/voice/stream", data, {
        responseType: "text",
        reportProgress: true,
        observe: "events"
      })
      .subscribe({
        next: e => {
          switch (e.type) {
            case HttpEventType.DownloadProgress: {
              if (!(e as HttpDownloadProgressEvent).partialText) {
                return;
              }

              // Clear the timeout once the first chunk is received
              if (lastResponseLength === 0) {
                clearTimeout(timeout); // Clear timeout here
              }

              const data = (e as HttpDownloadProgressEvent).partialText!.slice(lastResponseLength);
              const matches = data.match(/}/g);
              if (matches) {
                const lastIndex = data.lastIndexOf("}");
                const jsonString = data.substring(0, lastIndex + 1);
                const jsonParsed = this.parseSendVoice(jsonString);

                currentAssistantMessage = currentAssistantMessage + jsonParsed[0];
                currentSources.push(...jsonParsed[1]);
                existingAudio.push(...jsonParsed[2]);

                responseBS.next({
                  status: ResponseStatus.Pending,
                  assistant_response: currentAssistantMessage,
                  assistant_response_audio: existingAudio,
                  sources: currentSources
                });
                lastResponseLength += lastIndex + 1 || 0;
                return;
              } else {
                return;
              }
            }
            case HttpEventType.Response: {
              let existingData = responseBS.value;
              existingData!.status = ResponseStatus.Done;
              responseBS.next(existingData);
              return;
            }
          }
        },
        error: console.error
      });

    return responseBS;
  }

  /**
   * Method to send chat message to LLM for generation
   * @param message {Message} user message
   * @param profile {Profile}
   * @param history {Message[]} history of conversation for LLM context
   */
  async sendChat(message: Message, profile: Profile, history: Message[], language: string): Promise<BehaviorSubject<ChatResponse | null>> {
    const responseBS: BehaviorSubject<ChatResponse | null> = new BehaviorSubject<ChatResponse | null>(null);
    const responseId = createId();

    let lastResponseLength: number = 0;
    let currentResponseMessage: string = "";
    const currentSources: ApiSource[] = [];

    const data: ApiChatRequest = {
      chat_history: this.messageToApiChatHistory(history),
      profile: this.profileToApiProfile(profile),
      query: {
        role: "user",
        content: message.message
      },
      language: language.toLowerCase()
    };

    // Timeout setup
    const timeout = setTimeout(() => {
      console.log("Timed Out");
      responseBS.next({
        status: ResponseStatus.Timeout,
        response: currentResponseMessage,
        sources: currentSources
      });
      subscription.unsubscribe(); // Unsubscribe from the HTTP request
    }, APP_CONSTANTS.TEXT_TIMEOUT);

    // Subscription to the HttpClient request
    const subscription = this.httpClient
      .post("/chat/stream", data, {
        responseType: "text",
        reportProgress: true,
        observe: "events"
      })
      .subscribe({
        next: e => {
          switch (e.type) {
            case HttpEventType.DownloadProgress: {
              if (!(e as HttpDownloadProgressEvent).partialText) {
                return;
              }

              // Clear the timeout once the first chunk is received
              if (lastResponseLength === 0) {
                clearTimeout(timeout); // Clear timeout here
              }

              const currentResponseData = (e as HttpDownloadProgressEvent).partialText!.slice(lastResponseLength);
              const jsonParsed = this.parseSendChat(currentResponseData);
              currentResponseMessage += jsonParsed[0]; // Append the current response message
              currentSources.push(...jsonParsed[1]); // Append sources

              responseBS.next({
                status: ResponseStatus.Pending,
                response: currentResponseMessage,
                sources: currentSources
              });

              lastResponseLength = (e as HttpDownloadProgressEvent).partialText?.length || 0;
              break;
            }

            case HttpEventType.Response: {
              // No need to clear the timeout here since it's already done when the first chunk is received
              let latestData = responseBS.value;
              latestData!.status = ResponseStatus.Done;
              responseBS.next(latestData);
              break;
            }
          }
        },
        error: err => {
          clearTimeout(timeout); // Clear timeout if an error occurs
          console.error(err);
        }
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
      chat_history: this.messageToApiChatHistoryWithSources(feedback.chat_history)
    };

    console.log("Feedback data:", data);

    this.httpClient.post("/feedback", data).subscribe({
      next: () => {
        console.log("Feedback sent successfully");
      },
      error: console.error
    });
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

  private parseSendVoice(rawJsonString: string): any[] {
    let aggregatedResponseMessage: string = "";
    let aggregatedSources: [] = [];
    let aggregatedAudio: string[] = [];

    // Extract individual JSON objects
    const jsonObjects = this.extractJsonObjects(rawJsonString);
    // Process each JSON object
    for (const jsonObject of jsonObjects) {
      try {
        // Parse the JSON object
        const data = JSON.parse(jsonObject);

        // Extract and append the response message
        const responseMessage: string = data.response_message || "";
        const audioMessage: string = data.audio_base64 || "";
        const sources: [] = data.sources || [];
        aggregatedResponseMessage += responseMessage;
        aggregatedSources.push(...sources);
        if (audioMessage != "") {
          aggregatedAudio.push(audioMessage);
        }
      } catch (error) {
        console.error("Error decoding JSON:", error);
      }
    }
    return [aggregatedResponseMessage, aggregatedSources, aggregatedAudio];
  }
}
