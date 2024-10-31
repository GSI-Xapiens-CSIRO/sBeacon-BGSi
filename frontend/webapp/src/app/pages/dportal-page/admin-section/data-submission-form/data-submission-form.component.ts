import { Component, ViewChild } from '@angular/core';
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
import { DportalService } from '../../../../services/dportal.service';
import { SpinnerService } from 'src/app/services/spinner.service';
import { catchError, of, switchMap, tap } from 'rxjs';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import {
  FileDropEvent,
  FileDropperComponent,
} from './file-dropper/file-dropper.component';
import { Storage } from 'aws-amplify';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { forkJoin } from 'rxjs';

interface DataFormType {
  projectName: string;
  projectDescription: string;
  vcf: File;
  tbi: File;
  json: File;
}

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
    FileDropperComponent,
    MatProgressSpinnerModule,
  ],
  templateUrl: './data-submission-form.component.html',
  styleUrl: './data-submission-form.component.scss',
})
export class DataSubmissionFormComponent {
  @ViewChild(FileDropperComponent) fileDroppper!: FileDropperComponent;
  dataSubmissionForm: FormGroup;
  totalSize = 0;
  progress = 0;

  constructor(
    private fb: FormBuilder,
    private dps: DportalService,
    private ss: SpinnerService,
    private sb: MatSnackBar,
  ) {
    this.dataSubmissionForm = this.fb.group({
      projectName: fb.control('', [
        Validators.required,
        Validators.pattern(/^\S.*\S$/),
      ]),
      projectDescription: fb.control('', Validators.required),
      vcf: fb.control(null, Validators.required),
      tbi: fb.control(null, Validators.required),
      json: fb.control(null, Validators.required),
    });
  }

  async uploadFile(path: string, file: File): Promise<string> {
    try {
      await Storage.put(`projects/${path}/${file.name}`, file, {
        customPrefix: { public: '' },
        progressCallback: (progress: { loaded: number; total: number }) => {
          this.progress += progress.loaded;
        },
      });
    } catch (error) {
      console.error('Error uploading file', error);
      throw error;
    }
    return `projects/${path}/${file.name}`;
  }

  async onSubmit(entry: any) {
    this.dataSubmissionForm.disable();
    const projectName = entry.projectName;
    const projectDescription = entry.projectDescription;
    this.progress = 0;
    this.totalSize =
      (entry.vcf as File).size +
      (entry.tbi as File).size +
      (entry.json as File).size;
    forkJoin([
      this.uploadFile(projectName, entry.vcf),
      this.uploadFile(projectName, entry.tbi),
      this.uploadFile(projectName, entry.json),
    ])
      .pipe(
        catchError(() => of(null)),
        switchMap((res) => {
          if (res) {
            const [vcf, tbi, json] = res;

            return this.dps
              .adminCreateProject(
                projectName,
                projectDescription,
                vcf,
                tbi,
                json,
              )
              .pipe(catchError(() => of(null)));
          }
          return of(null);
        }),
      )
      .subscribe((res: any) => {
        if (!res) {
          this.sb.open('Project creation failed', 'Okay', { duration: 60000 });
        } else {
          this.sb.open('Project created', 'Okay', { duration: 60000 });
        }
        this.reset();
      });
  }

  patchFiles(event: FileDropEvent) {
    this.dataSubmissionForm.patchValue(event);
  }

  reset() {
    this.dataSubmissionForm.reset();
    this.dataSubmissionForm.enable();
    this.fileDroppper.reset();
    this.progress = 0;
    this.totalSize = 0;
  }
}
