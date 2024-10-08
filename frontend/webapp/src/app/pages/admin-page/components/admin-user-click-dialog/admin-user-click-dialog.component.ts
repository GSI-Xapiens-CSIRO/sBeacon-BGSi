import { Component, Inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';

import {
  MAT_DIALOG_DATA,
  MatDialog,
  MatDialogModule,
  MatDialogRef,
} from '@angular/material/dialog';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatButtonModule } from '@angular/material/button';
import {
  FormBuilder,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
} from '@angular/forms';
import { AdminService } from 'src/app/pages/admin-page/services/admin.service';
import { catchError, of } from 'rxjs';
import * as _ from 'lodash';
import { ComponentSpinnerComponent } from 'src/app/components/component-spinner/component-spinner.component';

@Component({
  selector: 'app-admin-user-click-dialog',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatCheckboxModule,
    MatButtonModule,
    FormsModule,
    ReactiveFormsModule,
    ComponentSpinnerComponent,
  ],
  templateUrl: './admin-user-click-dialog.component.html',
  styleUrls: ['./admin-user-click-dialog.component.scss'],
  providers: [AdminService],
})
export class AdminUserClickDialogComponent implements OnInit {
  protected initialGroups: any = {
    admin: false,
    record: false,
    count: false,
    boolean: false,
  };
  protected form: FormGroup;
  protected loading = false;

  constructor(
    public dialogRef: MatDialogRef<AdminUserClickDialogComponent>,
    private fb: FormBuilder,
    private as: AdminService,
    private dg: MatDialog,
    @Inject(MAT_DIALOG_DATA) public data: any,
  ) {
    this.form = this.fb.group({
      admin: [false],
      record: [false],
      count: [false],
      boolean: [false],
    });
  }

  ngOnInit(): void {
    this.loading = true;
    this.as
      .listUsersGroups(this.data.email)
      .pipe(catchError(() => of(null)))
      .subscribe((groups: any) => {
        const groupNames = _.map(
          _.get(groups, 'groups', []),
          (group) => _.split(group.GroupName, '-')[0],
        );
        const userGroups: { [key: string]: boolean } = {};
        _.each(groupNames, (gn: string) => {
          userGroups[gn] = true;
        });
        _.merge(this.initialGroups, userGroups);
        this.form.patchValue(userGroups);
        this.loading = false;
      });
  }

  async delete() {
    const { ActionConfirmationDialogComponent } = await import(
      '../../../../components/action-confirmation-dialog/action-confirmation-dialog.component'
    );

    const dialog = this.dg.open(ActionConfirmationDialogComponent, {
      data: {
        title: 'Delete User',
        message: 'Are you sure you want to delete this user?',
      },
    });
    dialog.afterClosed().subscribe((result) => {
      if (result) {
        this.loading = true;
        this.as
          .deleteUser(this.data.email)
          .pipe(catchError(() => of(null)))
          .subscribe(() => {
            this.loading = false;
            this.dialogRef.close({ reload: true });
          });
      }
    });
  }

  cancel(): void {
    this.dialogRef.close();
  }

  done(): void {
    if (_.isEqual(this.initialGroups, this.form.value)) {
      this.dialogRef.close();
      return;
    }

    this.loading = true;
    this.as
      .updateUsersGroups(this.data.email, this.form.value)
      .pipe(catchError(() => of(null)))
      .subscribe(() => {
        this.loading = false;
        this.dialogRef.close();
      });
  }
}
