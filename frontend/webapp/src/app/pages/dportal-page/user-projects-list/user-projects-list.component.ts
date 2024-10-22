import { Component } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-user-projects-list',
  standalone: true,
  imports: [MatButtonModule, MatIconModule],
  templateUrl: './user-projects-list.component.html',
  styleUrl: './user-projects-list.component.scss',
})
export class UserProjectsListComponent {}
