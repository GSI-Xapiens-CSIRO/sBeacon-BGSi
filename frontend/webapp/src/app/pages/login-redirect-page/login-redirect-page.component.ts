import { Component, OnInit } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { ComponentSpinnerComponent } from 'src/app/components/component-spinner/component-spinner.component';
import { ActivatedRoute } from '@angular/router';
import { AuthService } from 'src/app/services/auth.service';

@Component({
  selector: 'app-login-redirect-page',
  standalone: true,
  imports: [MatCardModule, ComponentSpinnerComponent],
  templateUrl: './login-redirect-page.component.html',
  styleUrl: './login-redirect-page.component.scss',
})
export class LoginRedirectPageComponent implements OnInit {
  constructor(
    private route: ActivatedRoute,
    private auth: AuthService,
  ) {}

  ngOnInit(): void {
    this.route.queryParams.subscribe((params) => {
      console.log('ID Token:', params['idToken']);
      console.log('Access Token:', params['accessToken']);
      console.log('Refresh Token:', params['refreshToken']);
      this.auth
        .tokenSignIn(
          params['idToken'],
          params['accessToken'],
          params['refreshToken'],
        )
        .then((success) => {
          console.log('success', success);
        });

      // Handle the query parameters as needed
    });
  }
}
