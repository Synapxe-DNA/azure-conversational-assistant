import { AfterViewChecked, Component, ElementRef, Input, OnInit, ViewChild } from "@angular/core";
import { MessageRole } from "../../types/message.type";
import { BehaviorSubject, takeWhile } from "rxjs";
import { Profile } from "../../types/profile.type";
import { Message } from "../../types/message.type";
import { ChatMessageService } from "../../services/chat-message/chat-message.service";
import { ProfileService } from "../../services/profile/profile.service";
import { ActivatedRoute } from "@angular/router";
import { TextUserComponent } from "../text/text-user/text-user.component";
import { TextSystemComponent } from "../text/text-system/text-system.component";
import { TextInputComponent } from "../text/text-input/text-input.component";
import { StickyBottomDirective } from "../../directives/stick-bottom/sticky-bottom.directive";
import { LoadingComponent } from "../loading/loading.component";
import { APP_CONSTANTS } from "../../constants";
import { CommonModule } from "@angular/common";
import { ChatMode } from "../../types/chat-mode.type";
import { PreferenceService } from "../../services/preference/preference.service";
import { Button } from "primeng/button";

@Component({
  selector: "app-text-mobile",
  standalone: true,
  imports: [TextUserComponent, TextSystemComponent, TextInputComponent, LoadingComponent, StickyBottomDirective, CommonModule, Button],
  templateUrl: "./text-mobile.component.html",
  styleUrl: "./text-mobile.component.css"
})
export class TextMobileComponent implements OnInit, AfterViewChecked {
  @Input() showTextInput?: boolean = true;

  @ViewChild("messageContainer") private messageContainer!: ElementRef;

  user: string = MessageRole.User;
  system: string = MessageRole.Assistant;
  profile: BehaviorSubject<Profile | undefined> = new BehaviorSubject<Profile | undefined>(undefined);
  chatMode?: ChatMode;

  messages: Message[] = [];
  loading: boolean = false;
  timeout: boolean = false;
  private timeoutId: any; // Store the timeout reference
  private autoScroll: boolean = true;

  constructor(
    private chatMessageService: ChatMessageService,
    private profileService: ProfileService,
    private route: ActivatedRoute,
    private preferences: PreferenceService
  ) {
    this.preferences.$chatMode.subscribe(m => {
      this.chatMode = m;
    });
  }

  ngOnInit(): void {
    this.route.paramMap.pipe(takeWhile(p => p.get("profileId") !== undefined, true)).subscribe(p => {
      this.profile = this.profileService.getProfile(p.get("profileId")!);
    });

    this.autoScroll = true;

    this.profile.subscribe(p => {
      if (!p) {
        return;
      }
      this.chatMessageService.load(p.id).then(m => {
        m.subscribe(messages => {
          this.messages = messages;
          this.timeout = false;
          this.onScroll();

          // Check the most recent message (last element in the array)
          const mostRecentMessage = messages[messages.length - 1];
          if (mostRecentMessage && mostRecentMessage.role === MessageRole.Assistant) {
            this.loading = false; // Stop loading if the most recent message is from Assistant

            // Clear the timeout to stop the timeout message from showing
            if (this.timeoutId) {
              clearTimeout(this.timeoutId);
              this.timeoutId = null; // Reset the timeout reference
            }
          }
        });
        this.autoScroll = true;
      });
    });
  }

  ngAfterViewChecked(): void {
    if (this.autoScroll) {
      this.scrollToBottom();
      this.autoScroll = false;
    }
  }

  onMessageSent(isError: boolean) {
    if (isError) {
      this.loading = false; // Hide the loading indicator after processing
      if (this.timeoutId) {
        clearTimeout(this.timeoutId);
        this.timeoutId = null; // Reset the timeout reference
      }
      this.showTimeoutMessage();
    } else {
      console.log("Message sent");
      this.loading = true;
      this.autoScroll = true;
      // Simulate message processing with a timeout
      this.timeoutId = setTimeout(() => {
        this.loading = false; // Hide the loading indicator after processing
        this.showTimeoutMessage(); // Show timeout message if Assistant's message isn't received
      }, APP_CONSTANTS.TEXT_TIMEOUT); // Adjust the timeout duration as needed
    }
  }

  toggleChatMode() {
    switch (this.chatMode) {
      case ChatMode.Voice:
        this.preferences.setChatMode(ChatMode.Text);
        break;
      case ChatMode.Text:
        this.preferences.setChatMode(ChatMode.Voice);
        break;
    }
  }

  showTimeoutMessage() {
    this.timeout = true;
  }

  scrollToBottom(): void {
    try {
      this.messageContainer.nativeElement.scrollTop = this.messageContainer.nativeElement.scrollHeight;
    } catch (err) {
      console.error("Error while scrolling to bottom:", err);
    }
  }

  onScroll() {
    const threshold = 2;
    const position = this.messageContainer.nativeElement.scrollTop + this.messageContainer.nativeElement.clientHeight;
    const height = this.messageContainer.nativeElement.scrollHeight;
    this.autoScroll = height - position <= threshold;
  }
}
