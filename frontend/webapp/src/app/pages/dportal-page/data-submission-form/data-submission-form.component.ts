import { Component } from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { DportalService } from '../../../services/dportal.service';
import { SpinnerService } from 'src/app/services/spinner.service';
import { catchError, of, tap } from 'rxjs';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

@Component({
  selector: 'app-data-submission-form',
  standalone: true,
  imports: [
    FormsModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatSnackBarModule,
  ],
  templateUrl: './data-submission-form.component.html',
  styleUrl: './data-submission-form.component.scss',
})
export class DataSubmissionFormComponent {
  dataSubmissionForm: FormGroup;
  constructor(
    private fb: FormBuilder,
    private dps: DportalService,
    private ss: SpinnerService,
    private sb: MatSnackBar,
  ) {
    this.dataSubmissionForm = this.fb.group({
      s3path: this.fb.control(null, [
        Validators.required,
        Validators.pattern(/^s3:\/\/([^\/]+)\/(.+)\.json$/i),
      ]),
    });
  }

  onSubmit(entry: any) {
    this.ss.start();
    this.dps
      .submitData(entry.s3path)
      .pipe(
        tap((res) => console.log(res)),
        catchError(() => of(null)),
      )
      .subscribe((res: any) => {
        if (!res) {
          this.sb.open('API request failed', 'Okay', { duration: 60000 });
        }
        this.ss.end();
      });
  }

  index() {
    this.ss.start();
    this.dps
      .indexData()
      .pipe(
        tap((res) => console.log(res)),
        catchError(() => of(null)),
      )
      .subscribe((res: any) => {
        if (!res) {
          this.sb.open('API request failed', 'Okay', { duration: 60000 });
        }
        this.ss.end();
      });
  }
}
