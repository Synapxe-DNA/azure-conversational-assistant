import { TestBed } from '@angular/core/testing';

import { ChatFollowupService } from './chat-followup.service';

describe('ChatFollowupService', () => {
  let service: ChatFollowupService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ChatFollowupService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
