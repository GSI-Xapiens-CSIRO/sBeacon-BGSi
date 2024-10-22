import { AsyncPipe } from '@angular/common';
import { Component } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { AuthService } from 'src/app/services/auth.service';
import { DataSubmissionFormComponent } from './data-submission-form/data-submission-form.component';
import { UserFileListComponent } from './user-file-list/user-file-list.component';
import { UserNotebookListComponent } from './user-notebook-list/user-notebook-list.component';
import { UserProjectsListComponent } from './user-projects-list/user-projects-list.component';

@Component({
  selector: 'app-dportal-page',
  standalone: true,
  imports: [
    MatCardModule,
    AsyncPipe,
    DataSubmissionFormComponent,
    UserFileListComponent,
    UserNotebookListComponent,
    UserProjectsListComponent,
  ],
  templateUrl: './dportal-page.component.html',
  styleUrl: './dportal-page.component.scss',
})
export class DportalPageComponent {
  constructor(protected auth: AuthService) {}
}
