import {
  Component,
  EventEmitter,
  Input,
  OnChanges,
  Output,
  SimpleChanges,
  ViewChild,
} from '@angular/core';
import { Project } from '../projects-list.component';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { FileDropperComponent } from '../../../file-dropper/file-dropper.component';
import {
  FormBuilder,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { DportalService } from 'src/app/services/dportal.service';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { DecimalPipe } from '@angular/common';
import { MatFormFieldModule } from '@angular/material/form-field';
import { catchError, forkJoin, map, of, switchMap } from 'rxjs';
import { Storage } from 'aws-amplify';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatInputModule } from '@angular/material/input';

@Component({
  selector: 'app-project-updates',
  standalone: true,
  imports: [
    MatButtonModule,
    MatIconModule,
    FileDropperComponent,
    MatSnackBarModule,
    DecimalPipe,
    MatFormFieldModule,
    FormsModule,
    MatInputModule,
    ReactiveFormsModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './project-updates.component.html',
  styleUrl: './project-updates.component.scss',
})
export class ProjectUpdatesComponent implements OnChanges {
  @Input({ required: true }) project!: Project;
  @Output() projectUpdated = new EventEmitter<void>();
  @ViewChild(FileDropperComponent) fileDroppper!: FileDropperComponent;
  dataSubmissionForm!: FormGroup;
  totalSize = 0;
  progress = 0;
  fileProgress = new Map<string, number>();
  addedFiles: File[] = [];
  removedFiles: string[] = [];

  constructor(
    private fb: FormBuilder,
    private dps: DportalService,
    private sb: MatSnackBar,
  ) {}

  ngOnChanges(changes: SimpleChanges): void {
    this.dataSubmissionForm = this.fb.group({
      projectDescription: this.fb.control(
        changes['project'].currentValue.description,
        Validators.required,
      ),
    });
  }

  removeFile(file: string) {
    if (!this.removedFiles.includes(file)) {
      this.removedFiles.push(file);
    }
  }

  removeFileFromForm(index: number) {
    this.addedFiles.splice(index, 1);
  }

  undoRemoveFile(index: number) {
    this.removedFiles.splice(index, 1);
  }

  submitDisabled(entry: any) {
    if (this.dataSubmissionForm.invalid || this.dataSubmissionForm.disabled) {
      return true;
    }

    if (
      this.addedFiles.length === 0 &&
      this.removedFiles.length === 0 &&
      entry.projectDescription === this.project.description
    ) {
      return true;
    }

    return false;
  }

  patchFiles(files: FileList) {
    if (files.length + this.addedFiles.length > 20) {
      this.sb.open('No more than 20 files per project is allowed!', 'Okay', {
        duration: 60000,
      });
      return;
    }
    this.addedFiles = [...this.addedFiles, ...Array.from(files)];
  }

  reset() {
    console.log('reset');
    this.dataSubmissionForm.reset({
      projectDescription: this.project.description,
    });
    this.dataSubmissionForm.enable();
    this.progress = 0;
    this.totalSize = 0;
    this.fileProgress.clear();
    this.addedFiles = [];
    this.removedFiles = [];
  }

  async uploadFile(path: string, file: File): Promise<string> {
    this.fileProgress.set(file.name, 0);
    try {
      await Storage.put(`projects/${path}/${file.name}`, file, {
        customPrefix: { public: '' },
        progressCallback: (progress: { loaded: number; total: number }) => {
          this.fileProgress.set(file.name, progress.loaded);
          this.progress = Array.from(this.fileProgress.values()).reduce(
            (acc, val) => acc + val,
            0,
          );
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
    this.progress = 0;
    this.totalSize = this.addedFiles.reduce((acc, file) => acc + file.size, 0);
    this.dps
      .adminUpdateProject(this.project.name, entry.projectDescription, [
        ...this.addedFiles.map((file) => file.name),
        ...this.project.files.filter(
          (file) => !this.removedFiles.includes(file),
        ),
      ])
      .pipe(
        catchError(() => of(null)),
        switchMap((res: any) => {
          if (res) {
            return forkJoin(
              this.addedFiles.map((file) =>
                this.uploadFile(this.project.name, file),
              ),
            ).pipe(
              catchError(() => of(null)),
              map(() => of(res)),
            );
          }
          return of(null);
        }),
      )
      .subscribe((res: any) => {
        console.log(res);
        if (!res) {
          this.sb.open('Project update failed', 'Okay', { duration: 60000 });
        } else {
          this.sb.open('Project updated', 'Okay', { duration: 60000 });
          this.reset();
          this.projectUpdated.emit();
        }
      });
  }
}
