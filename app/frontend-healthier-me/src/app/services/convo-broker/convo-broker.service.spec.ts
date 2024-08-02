import { TestBed } from "@angular/core/testing";

import { ConvoBrokerService } from "./convo-broker.service";

describe("ConvoBrokerService", () => {
  let service: ConvoBrokerService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ConvoBrokerService);
  });

  it("should be created", () => {
    expect(service).toBeTruthy();
  });
});
