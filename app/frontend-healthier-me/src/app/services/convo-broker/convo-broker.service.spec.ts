import { TestBed } from "@angular/core/testing";

import { ConvoBrokerService } from "./convo-broker.service";
import { NgxIndexedDBModule, NgxIndexedDBService } from "ngx-indexed-db";
import { NgxIndexedDbConfig } from "../../configs/ngx-indexed-db/ngx-indexed-db.config";
import { ChatMessageService } from "../chat-message/chat-message.service";
import { AudioPlayerService } from "../audio-player/audio-player.service";
import { EndpointService } from "../endpoint/endpoint.service";

describe("ConvoBrokerService", () => {
    let service: ConvoBrokerService;

    beforeEach(() => {
        TestBed.configureTestingModule({
            imports: [NgxIndexedDBModule.forRoot(NgxIndexedDbConfig)],
            providers: [ChatMessageService, AudioPlayerService, EndpointService, NgxIndexedDBService]
        });
        service = TestBed.inject(ConvoBrokerService);
    });

    it("should be created", () => {
        expect(service).toBeTruthy();
    });
});
