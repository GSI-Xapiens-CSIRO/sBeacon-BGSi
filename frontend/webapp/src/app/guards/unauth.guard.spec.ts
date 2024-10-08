import { TestBed } from '@angular/core/testing';
import { CanDeactivateFn } from '@angular/router';

import { unauthGuard } from './unauth.guard';

describe('unauthGuard', () => {
  const executeGuard: CanDeactivateFn = (...guardParameters) =>
    TestBed.runInInjectionContext(() => unauthGuard(...guardParameters));

  beforeEach(() => {
    TestBed.configureTestingModule({});
  });

  it('should be created', () => {
    expect(executeGuard).toBeTruthy();
  });
});
