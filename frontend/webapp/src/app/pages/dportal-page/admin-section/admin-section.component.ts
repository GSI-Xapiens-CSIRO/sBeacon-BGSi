import { Component } from '@angular/core';
import { DataSubmissionFormComponent } from './data-submission-form/data-submission-form.component';
import { MatCardModule } from '@angular/material/card';
import { MatTabsModule } from '@angular/material/tabs';
import { ProjectsListComponent } from './projects-list/projects-list.component';
import { NotebooksComponent } from './admin-notebooks-list/admin-notebooks-list.component';

@Component({
  selector: 'app-admin-section',
  standalone: true,
  imports: [
    DataSubmissionFormComponent,
    MatCardModule,
    MatTabsModule,
    ProjectsListComponent,
    NotebooksComponent,
  ],
  templateUrl: './admin-section.component.html',
  styleUrl: './admin-section.component.scss',
})
export class AdminSectionComponent {}
