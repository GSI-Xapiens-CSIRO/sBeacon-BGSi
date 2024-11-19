import { Component, EventEmitter, Input, Output } from '@angular/core';
import {
  FormControl,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { catchError, of } from 'rxjs';
import { DportalService } from 'src/app/services/dportal.service';

@Component({
  selector: 'app-project-assignments',
  standalone: true,
  imports: [
    MatFormFieldModule,
    MatInputModule,
    ReactiveFormsModule,
    FormsModule,
    MatButtonModule,
    MatIconModule,
    MatSnackBarModule,
  ],
  templateUrl: './project-assignments.component.html',
  styleUrl: './project-assignments.component.scss',
})
export class ProjectAssignmentsComponent {
  @Input({ required: true }) project!: string;
  email = new FormControl('', [Validators.required, Validators.email]);

  constructor(
    private dps: DportalService,
    private sb: MatSnackBar,
  ) {}

  submit(email: string) {
    console.log(this.project, email);
    this.dps
      .adminAddUserToProject(this.project, email)
      .pipe(catchError(() => of(null)))
      .subscribe((res: any) => {
        if (!res) {
          this.sb.open('Unable to add user. Please check email.', 'Close', {
            duration: 60000,
          });
        } else {
          this.sb.open('User added successfully.', 'Close', {
            duration: 60000,
          });
          this.email.reset();
        }
      });
  }
}
