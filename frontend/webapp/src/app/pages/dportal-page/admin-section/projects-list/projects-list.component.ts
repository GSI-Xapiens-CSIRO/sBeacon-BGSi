import { Component } from '@angular/core';
import { ComponentSpinnerComponent } from 'src/app/components/component-spinner/component-spinner.component';
import { DportalService } from 'src/app/services/dportal.service';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { SpinnerService } from 'src/app/services/spinner.service';
import { MatSnackBar } from '@angular/material/snack-bar';
import { catchError, of, tap } from 'rxjs';
import { MatIconModule } from '@angular/material/icon';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { ProjectAssignmentsComponent } from './project-assignments/project-assignments.component';
import { ProjectsUsersComponent } from './projects-users/projects-users.component';

interface Project {
  name: string;
  description: string;
  files: string[];
  indexed: boolean;
}

@Component({
  selector: 'app-projects-list',
  standalone: true,
  imports: [
    ComponentSpinnerComponent,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatDialogModule,
    ProjectAssignmentsComponent,
    ProjectsUsersComponent,
  ],
  templateUrl: './projects-list.component.html',
  styleUrl: './projects-list.component.scss',
})
export class ProjectsListComponent {
  loading = true;
  dataSource = new MatTableDataSource<Project>();
  displayedColumns: string[] = [
    'name',
    'description',
    'files',
    'indexed',
    'actions',
  ];
  assignTo: string | null = null;
  viewUsers: string | null = null;

  constructor(
    private dps: DportalService,
    private ss: SpinnerService,
    private sb: MatSnackBar,
    private dg: MatDialog,
  ) {
    this.list();
  }

  list() {
    this.dps
      .getProjects()
      .pipe(catchError(() => of(null)))
      .subscribe((data: any[]) => {
        if (!data) {
          this.sb.open('API request failed', 'Okay', { duration: 60000 });
          this.dataSource.data = [];
        } else {
          this.dataSource.data = data.map((project) => ({
            name: project.name,
            description: project.description,
            files: [project.vcf, project.tbi, project.json],
            indexed: false,
          }));
        }
        this.loading = false;
      });
  }

  index() {
    this.ss.start();
    this.dps
      .indexData()
      .pipe(catchError(() => of(null)))
      .subscribe((res: any) => {
        if (!res) {
          this.sb.open('API request failed', 'Okay', { duration: 60000 });
        }
        this.ss.end();
      });
  }

  async delete(name: string) {
    const { ActionConfirmationDialogComponent } = await import(
      '../../../../components/action-confirmation-dialog/action-confirmation-dialog.component'
    );

    const dialog = this.dg.open(ActionConfirmationDialogComponent, {
      data: {
        title: 'Delete Project',
        message: 'Are you sure you want to delete this project?',
      },
    });
    dialog.afterClosed().subscribe((result) => {
      if (result) {
        this.dps
          .deleteProject(name)
          .pipe(catchError(() => of(null)))
          .subscribe((res: any) => {
            if (!res) {
              this.sb.open('Unable to delete project.', 'Close', {
                duration: 60000,
              });
            }
            this.list();
          });
      }
    });
  }

  async ingest(name: string) {
    const { ActionConfirmationDialogComponent } = await import(
      '../../../../components/action-confirmation-dialog/action-confirmation-dialog.component'
    );

    const dialog = this.dg.open(ActionConfirmationDialogComponent, {
      data: {
        title: 'Ingest Project',
        message: 'Are you sure you want to ingest this project to sBeacon?',
      },
    });
    dialog.afterClosed().subscribe((result) => {
      if (result) {
        this.sb.open('Not implemented', 'Okay', { duration: 60000 });
      }
    });
  }
}
