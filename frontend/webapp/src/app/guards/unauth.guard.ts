import { CanActivateFn } from '@angular/router';
import { Auth } from 'aws-amplify';
import { inject } from '@angular/core';
import { Router } from '@angular/router';

export const unauthGuard: CanActivateFn = async (route, state) => {
  const router = inject(Router);
  try {
    await Auth.currentAuthenticatedUser();
    return router.parseUrl('/');
  } catch (error) {
    return true;
  }
};
