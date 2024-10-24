import { Component, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatOptionModule } from '@angular/material/core';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { instanceTypes, volumeSizes } from './data';
import {
  FormBuilder,
  FormGroup,
  FormGroupDirective,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { MatInputModule } from '@angular/material/input';
import { DportalService } from 'src/app/services/dportal.service';
import { catchError, of } from 'rxjs';
import { NotebookItemComponent } from './notebook-item/notebook-item.component';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import {
  MatExpansionModule,
  MatExpansionPanel,
} from '@angular/material/expansion';

export type InstanceName = string;

export interface InstanceStartInfo {
  instanceName: string;
  instanceType: string;
  volumeSize: number;
}

@Component({
  selector: 'app-user-notebook-list',
  standalone: true,
  imports: [
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatSelectModule,
    MatOptionModule,
    FormsModule,
    ReactiveFormsModule,
    MatInputModule,
    NotebookItemComponent,
    MatSnackBarModule,
    MatExpansionModule,
  ],
  templateUrl: './user-notebook-list.component.html',
  styleUrl: './user-notebook-list.component.scss',
})
export class UserNotebookListComponent implements OnInit {
  notebooks: InstanceName[] = [];
  instanceTypes = instanceTypes;
  volumeSizes = volumeSizes;
  instanceForm: FormGroup;
  loading = false;

  constructor(
    fb: FormBuilder,
    private dps: DportalService,
    private sb: MatSnackBar,
  ) {
    this.instanceForm = fb.group({
      instanceName: fb.control('', [
        Validators.required,
        Validators.minLength(5),
        Validators.maxLength(30),
        Validators.pattern('^[a-zA-Z0-9-]+$'),
      ]),
      instanceType: fb.control('', [Validators.required]),
      volumeSize: fb.control('', [Validators.required]),
    });
  }

  ngOnInit(): void {
    this.list();
  }

  list() {
    this.loading = true;
    this.dps
      .getMyNotebooks()
      .pipe(catchError(() => of(null)))
      .subscribe((notebooks: InstanceName[]) => {
        if (notebooks) {
          this.notebooks = notebooks;
        }
        this.loading = false;
      });
  }

  create(info: InstanceStartInfo, panel: MatExpansionPanel) {
    this.dps
      .createNotebookInstance(
        info.instanceName,
        info.instanceType,
        info.volumeSize,
      )
      .pipe(catchError(() => of(null)))
      .subscribe((res) => {
        if (!res) {
          this.sb.open('Failed to create notebook', 'Close', {
            duration: 60000,
          });
        }
        this.list();
        this.instanceForm.reset();
        panel.close();
      });
  }

  reset() {
    console.log(this.instanceForm);
  }

  remove(notebook: InstanceName) {
    this.notebooks = this.notebooks.filter((n) => n !== notebook);
  }
}
