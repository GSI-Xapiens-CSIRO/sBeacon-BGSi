import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { Auth } from 'aws-amplify';

export const authGuard: CanActivateFn = async (route, state) => {
  const router = inject(Router);
  try {
    await Auth.currentAuthenticatedUser();
    return true;
  } catch (error) {
    return router.parseUrl('/login');
  }
};
