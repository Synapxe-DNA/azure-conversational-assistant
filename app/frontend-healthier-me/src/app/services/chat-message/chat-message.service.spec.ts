import {TestBed} from "@angular/core/testing"

import {ChatMessageService} from "./chat-message.service"
import {NgxIndexedDBModule, NgxIndexedDBService} from "ngx-indexed-db";
import {NgxIndexedDbConfig} from "../../configs/ngx-indexed-db/ngx-indexed-db.config";
import {Message, MessageRole} from "../../types/message.type";
import {firstValueFrom} from "rxjs";
import {createId} from "@paralleldrive/cuid2";

describe("ChatMessageService", () => {
  let service: ChatMessageService

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [NgxIndexedDBModule.forRoot(NgxIndexedDbConfig)],
      providers: [NgxIndexedDBService]
    })
    service = TestBed.inject(ChatMessageService)
  })

  it("should be created", () => {
    expect(service).toBeTruthy()
  })

})
