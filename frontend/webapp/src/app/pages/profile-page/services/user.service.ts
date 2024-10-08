import { Injectable } from '@angular/core';
import { Auth } from 'aws-amplify';
import { from } from 'rxjs';

@Injectable()
export class UserService {
  constructor() {}

  updateDetails(firstName: string, lastName: string) {
    return from(
      (async () => {
        const user = await Auth.currentAuthenticatedUser();
        const result = await Auth.updateUserAttributes(user, {
          given_name: firstName,
          family_name: lastName,
        });
        return result;
      })(),
    );
  }

  updatePassword(oldPassword: string, newPassword: string) {
    return from(
      (async () => {
        const user = await Auth.currentAuthenticatedUser();
        const result = await Auth.changePassword(
          user,
          oldPassword,
          newPassword,
        );
        return result;
      })(),
    );
  }
}
