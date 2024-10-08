import { CommonModule } from '@angular/common';
import { AfterViewInit, Component, Inject, ViewChild } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import {
  MatCheckboxChange,
  MatCheckboxModule,
} from '@angular/material/checkbox';
import {
  MAT_DIALOG_DATA,
  MatDialogModule,
  MatDialogRef,
} from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatPaginator, MatPaginatorModule } from '@angular/material/paginator';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import * as _ from 'lodash';

@Component({
  selector: 'app-term-picker-dialog',
  templateUrl: './term-picker-dialog.component.html',
  styleUrl: './term-picker-dialog.component.scss',
  standalone: true,
  imports: [
    CommonModule,
    MatCheckboxModule,
    MatCardModule,
    MatPaginatorModule,
    MatDialogModule,
    MatTableModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
  ],
})
export class TermPickerDialogComponent implements AfterViewInit {
  @ViewChild('paginator')
  paginator!: MatPaginator;
  protected selected: string[] = [];
  protected terms: MatTableDataSource<any>;
  protected columns: any[] = ['selected', 'id', 'label'];
  protected _ = _;

  constructor(
    public dialogRef: MatDialogRef<TermPickerDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
  ) {
    this.terms = new MatTableDataSource<any>(data.terms);
    this.selected = data.selected;
  }

  ngAfterViewInit(): void {
    this.terms.paginator = this.paginator;
  }

  cancel(): void {
    this.dialogRef.close([]);
  }

  done(): void {
    this.dialogRef.close(this.selected);
  }

  select(item: any, event: MatCheckboxChange) {
    if (event.checked) {
      this.selected = [...new Set([...this.selected, item.id])];
    } else {
      this.selected = _.filter(this.selected, (i) => i !== item.id);
    }
  }

  applyFilter(event: Event) {
    const filterValue = (event.target as HTMLInputElement).value;
    this.terms.filter = filterValue.trim().toLowerCase();
  }
}
