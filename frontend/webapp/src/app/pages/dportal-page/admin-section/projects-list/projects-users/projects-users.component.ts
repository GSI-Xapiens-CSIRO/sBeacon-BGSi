import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { catchError, of } from 'rxjs';
import { DportalService } from 'src/app/services/dportal.service';

interface User {
  firstName: string;
  lastName: string;
  email: string;
}

@Component({
  selector: 'app-projects-users',
  standalone: true,
  imports: [
    MatIconModule,
    MatButtonModule,
    MatTableModule,
    MatSnackBarModule,
    MatDialogModule,
  ],
  templateUrl: './projects-users.component.html',
  styleUrl: './projects-users.component.scss',
})
export class ProjectsUsersComponent implements OnInit {
  @Output() closed = new EventEmitter<void>();
  @Input({ required: true }) project!: string;

  displayedColumns: string[] = ['firstName', 'lastName', 'email', 'actions'];
  dataSource = new MatTableDataSource<User>();

  constructor(
    private dps: DportalService,
    private sb: MatSnackBar,
    private dg: MatDialog,
  ) {}

  ngOnInit(): void {
    this.list();
  }

  list() {
    this.dps
      .getProjectUsers(this.project!)
      .pipe(catchError(() => of(null)))
      .subscribe((users: User[] | null) => {
        if (!users) {
          this.sb.open('Unable to add user. Please check email.', 'Close', {
            duration: 60000,
          });
        } else {
          this.dataSource.data = users;
        }
      });
  }

  async unAssignUser(email: string) {
    const { ActionConfirmationDialogComponent } = await import(
      '../../../../../components/action-confirmation-dialog/action-confirmation-dialog.component'
    );

    const dialog = this.dg.open(ActionConfirmationDialogComponent, {
      data: {
        title: 'Remove User',
        message: 'Are you sure you want to remove this user from project?',
      },
    });
    dialog.afterClosed().subscribe((result) => {
      if (result) {
        this.dps
          .removeUserFromProject(this.project, email)
          .pipe(catchError(() => of(null)))
          .subscribe((res: any) => {
            if (!res) {
              this.sb.open('Unable to remove user.', 'Close', {
                duration: 60000,
              });
            }
            this.list();
          });
      }
    });
  }
}
