import { TestBed } from "@angular/core/testing";

import { ChatMessageService } from "./chat-message.service";
import { NgxIndexedDBModule, NgxIndexedDBService } from "ngx-indexed-db";
import { NgxIndexedDbConfig } from "../../configs/ngx-indexed-db/ngx-indexed-db.config";
import { Message, MessageRole } from "../../types/message.type";
import { firstValueFrom } from "rxjs";
import { createId } from "@paralleldrive/cuid2";

describe("ChatMessageService", () => {
  let service: ChatMessageService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [NgxIndexedDBModule.forRoot(NgxIndexedDbConfig)],
      providers: [NgxIndexedDBService]
    });
    service = TestBed.inject(ChatMessageService);
  });

  it("should be created", () => {
    expect(service).toBeTruthy();
  });

  it("should update on insert", async () => {
    const randomProfileId = createId();
    const message: Message = {
      id: createId(),
      profile_id: randomProfileId,
      message: "Test message",
      timestamp: 1,
      role: MessageRole.User,
      sources: []
    };

    const initVal = (await service.load(randomProfileId)).value;
    expect(initVal).toEqual([]);

    await service.insert(message);

    const newVal = (await service.load(randomProfileId)).value;

    expect(newVal).toEqual([message]);
  });

  it("should update on upsert", async () => {
    const randomMessageId = createId();
    const randomProfileId = createId();
    const message: Message = {
      id: randomMessageId,
      profile_id: randomProfileId,
      message: "Test message",
      timestamp: 1,
      role: MessageRole.User,
      sources: []
    };

    const initVal = (await service.load(randomProfileId)).value;
    expect(initVal).toEqual([]);

    await service.insert(message);

    const newVal = (await service.load(randomProfileId)).value;

    expect(newVal).toEqual([message]);

    const newestMessage = {
      id: randomMessageId,
      profile_id: randomProfileId,
      message: "Test message that is longer",
      timestamp: 2,
      role: MessageRole.User,
      sources: []
    };

    await service.upsert(newestMessage);

    const newestVal = (await service.load(randomProfileId)).value;

    expect(newestVal).toEqual([newestMessage]);
  });
});
