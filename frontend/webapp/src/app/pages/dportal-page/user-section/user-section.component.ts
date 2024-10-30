import { Component } from '@angular/core';
import { UserProjectsListComponent } from './user-projects-list/user-projects-list.component';
import { UserNotebookListComponent } from './user-notebook-list/user-notebook-list.component';
import { UserFileListComponent } from './user-file-list/user-file-list.component';
import { MatCardModule } from '@angular/material/card';

@Component({
  selector: 'app-user-section',
  standalone: true,
  imports: [
    UserProjectsListComponent,
    UserNotebookListComponent,
    UserFileListComponent,
    MatCardModule,
  ],
  templateUrl: './user-section.component.html',
  styleUrl: './user-section.component.scss',
})
export class UserSectionComponent {}
