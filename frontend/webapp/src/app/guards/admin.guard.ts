import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { Auth } from 'aws-amplify';
import * as _ from 'lodash';

export const adminGuard: CanActivateFn = async (route, state) => {
  const router = inject(Router);
  try {
    const user = await Auth.currentAuthenticatedUser();
    const groups: string[] = _.get(
      user,
      'signInUserSession.accessToken.payload.cognito:groups',
      [],
    );

    return groups.includes('admin-group');
  } catch (error) {
    return router.parseUrl('/login');
  }
};
