import { Component } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  FormGroup,
  ValidationErrors,
  ValidatorFn,
  Validators,
  FormsModule,
  ReactiveFormsModule,
} from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import * as _ from 'lodash';
import { catchError, filter, of } from 'rxjs';
import { AuthService } from 'src/app/services/auth.service';
import { UserService } from './services/user.service';
import { MatSnackBar } from '@angular/material/snack-bar';
import { GlobalSpinnerComponent } from '../../components/global-spinner/global-spinner.component';
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatCardModule } from '@angular/material/card';
import { SpinnerService } from 'src/app/services/spinner.service';

/**
 * A validator function that checks if the 'confirmPassword' and 'newPassword' fields of a form match.
 */
const mustMatch = (): ValidatorFn => {
  return (control: AbstractControl): ValidationErrors | null => {
    // Check if 'confirmPassword' form control has any other errors.
    if (
      control.get('confirmPassword')?.errors &&
      !control.errors?.['confirmPassword']
    ) {
      return null;
    }
    const error = _.isEqual(
      control.get('confirmPassword')!.value,
      control.get('newPassword')!.value,
    )
      ? null
      : { mustMatch: 'Must match' };
    control.get('confirmPassword')?.setErrors(error);
    return error;
  };
};

/**
 * Validator function to check if 'oldPassword' and 'newPassword' do not match. If they match, an error is added to the 'newPassword' control.
 */
const mustNotMatch = (): ValidatorFn => {
  return (control: AbstractControl): ValidationErrors | null => {
    // Check if 'newPassword' form control has any other errors.
    if (
      control.get('newPassword')?.errors &&
      !control.errors?.['newPassword']
    ) {
      return null;
    }
    const error = _.isEqual(
      control.get('oldPassword')!.value,
      control.get('newPassword')!.value,
    )
      ? { mustNotMatch: 'Must not match' }
      : null;
    control.get('newPassword')?.setErrors(error);
    return error;
  };
};

@Component({
  selector: 'app-profile-page',
  templateUrl: './profile-page.component.html',
  styleUrl: './profile-page.component.scss',
  standalone: true,
  imports: [
    MatCardModule,
    FormsModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    GlobalSpinnerComponent,
  ],
  providers: [UserService],
})
export class ProfilePageComponent {
  protected user: any;
  protected userDetailsForm: FormGroup;
  protected userPasswordForm: FormGroup;

  constructor(
    private auth: AuthService,
    private fb: FormBuilder,
    private dg: MatDialog,
    private us: UserService,
    private sb: MatSnackBar,
    private ss: SpinnerService,
  ) {
    this.userDetailsForm = this.fb.group({
      firstName: ['', Validators.required],
      lastName: ['', Validators.required],
    });
    this.userPasswordForm = this.fb.group(
      {
        oldPassword: ['', [Validators.required, Validators.minLength(6)]],
        newPassword: ['', [Validators.required, Validators.minLength(6)]],
        confirmPassword: ['', [Validators.required, Validators.minLength(6)]],
      },
      { validators: [mustMatch(), mustNotMatch()] },
    );
    auth.user.pipe(filter((u) => !!u)).subscribe((u: any) => {
      this.user = u.signInUserSession.idToken.payload;
      this.resetDetails();
    });
  }

  resetDetails() {
    this.userDetailsForm.patchValue({
      firstName: this.user.given_name,
      lastName: this.user.family_name,
    });
    this.userDetailsForm.markAsPristine();
  }

  async updateDetails() {
    const { ActionConfirmationDialogComponent } = await import(
      '../../components/action-confirmation-dialog/action-confirmation-dialog.component'
    );
    const dialog = this.dg.open(ActionConfirmationDialogComponent, {
      data: {
        title: 'Update Details',
        message: 'Are you sure you want to update your details?',
      },
    });

    dialog.afterClosed().subscribe((yes) => {
      if (yes) {
        this.ss.start();
        this.us
          .updateDetails(
            this.userDetailsForm.value.firstName,
            this.userDetailsForm.value.lastName,
          )
          .pipe(
            catchError(() => {
              this.sb.open('Operation failed. Try again later.', 'Okay', {
                duration: 60000,
              });
              return of(null);
            }),
          )
          .subscribe((result) => {
            if (result === 'SUCCESS') {
              this.sb.open('Details updated successfully.', 'Okay', {
                duration: 60000,
              });
              this.resetDetails();
              this.auth.refresh();
            }
            this.ss.end();
          });
      }
    });
  }

  async updatePassword() {
    const { ActionConfirmationDialogComponent } = await import(
      '../../components/action-confirmation-dialog/action-confirmation-dialog.component'
    );
    const dialog = this.dg.open(ActionConfirmationDialogComponent, {
      data: {
        title: 'Update Password',
        message: 'Are you sure you want to update your password?',
      },
    });

    dialog.afterClosed().subscribe((yes) => {
      if (yes) {
        this.ss.start();
        this.us
          .updatePassword(
            this.userPasswordForm.value.oldPassword,
            this.userPasswordForm.value.newPassword,
          )
          .pipe(
            catchError(() => {
              this.sb.open('Operation failed. Try again later.', 'Okay', {
                duration: 60000,
              });
              return of(null);
            }),
          )
          .subscribe((result) => {
            if (result === 'SUCCESS') {
              this.sb.open('Password updated successfully.', 'Okay', {
                duration: 60000,
              });
              this.userPasswordForm.reset();
            }
            this.ss.end();
          });
      }
    });
  }
}
