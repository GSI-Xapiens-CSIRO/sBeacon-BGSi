import { Clipboard, ClipboardModule } from '@angular/cdk/clipboard';
import { Component, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { catchError, of } from 'rxjs';
import { DportalService } from 'src/app/services/dportal.service';

interface Project {
  name: string;
  description: string;
  files: string[];
  expanded: boolean;
}

@Component({
  selector: 'app-user-projects-list',
  standalone: true,
  imports: [
    MatButtonModule,
    MatIconModule,
    MatSnackBarModule,
    MatTooltipModule,
    ClipboardModule,
  ],
  templateUrl: './user-projects-list.component.html',
  styleUrl: './user-projects-list.component.scss',
})
export class UserProjectsListComponent implements OnInit {
  myProjects: Project[] = [];

  constructor(
    private dps: DportalService,
    private sb: MatSnackBar,
    private cb: Clipboard,
  ) {}

  ngOnInit(): void {
    this.list();
  }

  list() {
    this.dps
      .getMyProjects()
      .pipe(
        catchError((e) => {
          console.log(e);
          return of(null);
        }),
      )
      .subscribe((projects: any) => {
        if (!projects) {
          this.sb.open('Unable to get projects.', 'Close', {
            duration: 60000,
          });
        } else {
          this.myProjects = projects.map((p: Project) => ({
            ...p,
            expanded: false,
          }));
        }
      });
  }

  copy(project: string, prefix: string) {
    return this.dps
      .getMyProjectFile(project, prefix)
      .pipe(catchError(() => of(null)))
      .subscribe((url: string | null) => {
        if (!url) {
          this.sb.open('Unable to sign file.', 'Close', {
            duration: 60000,
          });
        } else {
          const pending = this.cb.beginCopy(url);
          let remainingAttempts = 3;
          const attempt = () => {
            const result = pending.copy();
            if (!result && --remainingAttempts) {
              setTimeout(attempt);
            } else {
              pending.destroy();
            }
          };
          attempt();
        }
      });
  }
}
