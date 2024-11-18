import { Injectable } from '@angular/core';
import { Auth, Hub } from 'aws-amplify';
import {
  CognitoUser,
  CognitoUserSession,
  CognitoIdToken,
  CognitoUserPool,
  CognitoAccessToken,
  CognitoRefreshToken,
} from 'amazon-cognito-identity-js';
import { BehaviorSubject } from 'rxjs';
import { Router } from '@angular/router';
import _ from 'lodash';
import { environment } from 'src/environments/environment';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  public user = new BehaviorSubject<CognitoUser | null>(null);
  public userGroups = new BehaviorSubject<Set<string>>(new Set([]));
  private tempUser: any = null;

  constructor(private router: Router) {
    this.refresh();
  }

  async signIn(username: string, password: string) {
    try {
      const user = await Auth.signIn(username, password);

      if (_.get(user, 'challengeName', '') === 'NEW_PASSWORD_REQUIRED') {
        this.tempUser = user;
        return 'NEW_PASSWORD_REQUIRED';
      }
      console.log('Logged in as ', user);
      await this.refresh();
      return true;
    } catch (error) {
      console.log('error signing in', error);
      return false;
    }
  }

  async tokenSignIn(
    idToken: string,
    accessToken: string,
    refreshToken: string,
  ) {
    try {
      // Decode ID token to get user information
      const decodedToken = JSON.parse(atob(idToken.split('.')[1]));
      const username = decodedToken['cognito:username'];
      // Configure Cognito User Pool
      const poolData = {
        UserPoolId: environment.auth.userPoolId, // Replace with your User Pool ID
        ClientId: environment.auth.userPoolWebClientId, // Replace with your App Client ID
      };
      // Create a CognitoUser instance
      const cognitoUser = new CognitoUser({
        Username: username,
        Pool: new CognitoUserPool(poolData),
      });
      const cognitoIdToken = new CognitoIdToken({ IdToken: idToken });
      const cognitoAccessToken = new CognitoAccessToken({
        AccessToken: accessToken,
      });
      const cognitoRefreshToken = new CognitoRefreshToken({
        RefreshToken: refreshToken,
      });
      // Create a CognitoUserSession manually
      const session = new CognitoUserSession({
        IdToken: cognitoIdToken,
        AccessToken: cognitoAccessToken,
        RefreshToken: cognitoRefreshToken,
      });
      // Inject the session into the CognitoUser object
      cognitoUser.setSignInUserSession(session);
      // Set the user in Amplify Auth for consistent app state
      await Auth.currentUserPoolUser(); // Triggers Amplify state sync
      this.refresh();
      this.router.navigate(['/']);
    } catch (error) {
      console.error('Error creating session:', error);
    }
  }

  async newPassword(newPassword: string) {
    await Auth.completeNewPassword(this.tempUser, newPassword);
    await this.refresh();
    return true;
  }

  async signOut() {
    await Auth.signOut({ global: true });
    this.refresh();
    this.router.navigate(['/']);
  }

  async refresh() {
    try {
      const user = await Auth.currentAuthenticatedUser();
      const sess = await Auth.currentSession();
      console.log(sess.getIdToken().getJwtToken());
      this.userGroups.next(
        new Set(user.signInUserSession.idToken.payload['cognito:groups']),
      );
      this.user.next(user);
      return true;
    } catch (error) {
      this.userGroups.next(new Set([]));
      this.user.next(null);
      return false;
    }
  }

  async forgotPassword(username: string) {
    return await Auth.forgotPassword(username);
  }
}
