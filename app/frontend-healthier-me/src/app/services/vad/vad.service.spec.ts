import { TestBed } from '@angular/core/testing';

import { VadService } from './vad.service';

/**
 * THIS TEST CASE IS IGNORED
 * (for now)
 *
 * Unable to send voice or access mic to test this in CI/CD yet, so there should not be any test cases here.
 * Tests here will cause the GH Action to time out and throw a "Browser Disconnection Error."
 */
describe('VadService', () => {
  // let service: VadService;
  //
  // beforeEach(() => {
  //   TestBed.configureTestingModule({});
  //   service = TestBed.inject(VadService);
  // });
  //
  // it('should be created', () => {
  //   expect(service).toBeTruthy();
  // });

  it("should not have any test cases", ()=>{
    expect(1).toBe(1)
  })
});
