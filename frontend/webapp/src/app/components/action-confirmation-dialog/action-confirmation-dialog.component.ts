import { Component, Inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import {
  MAT_DIALOG_DATA,
  MatDialogModule,
  MatDialogRef,
} from '@angular/material/dialog';

@Component({
  selector: 'app-action-confirmation-dialog',
  templateUrl: './action-confirmation-dialog.component.html',
  styleUrls: ['./action-confirmation-dialog.component.scss'],
  standalone: true,
  imports: [MatDialogModule, MatButtonModule],
})
export class ActionConfirmationDialogComponent {
  constructor(
    public dialogRef: MatDialogRef<ActionConfirmationDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
  ) {}
}
