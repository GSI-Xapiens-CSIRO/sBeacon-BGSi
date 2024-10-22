import { Component, Inject } from '@angular/core';
import {
  FormControl,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import {
  MAT_DIALOG_DATA,
  MatDialogModule,
  MatDialogRef,
} from '@angular/material/dialog';
import { MatInputModule } from '@angular/material/input';

export interface TextInputDialogComponentData {
  title: string;
  message: string;
  label: string;
  placeholder: string;
}

@Component({
  selector: 'app-text-input-dialog',
  standalone: true,
  imports: [
    MatDialogModule,
    MatButtonModule,
    MatInputModule,
    FormsModule,
    ReactiveFormsModule,
  ],
  templateUrl: './text-input-dialog.component.html',
  styleUrl: './text-input-dialog.component.scss',
})
export class TextInputDialogComponent {
  protected valueControl: FormControl = new FormControl('', [
    Validators.required,
    Validators.minLength(5),
    Validators.maxLength(64),
  ]);
  constructor(
    public dialogRef: MatDialogRef<TextInputDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: TextInputDialogComponentData,
  ) {}
}
