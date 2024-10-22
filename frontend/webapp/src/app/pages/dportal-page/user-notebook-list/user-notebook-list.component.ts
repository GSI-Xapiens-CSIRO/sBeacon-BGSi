import { Component } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-user-notebook-list',
  standalone: true,
  imports: [MatButtonModule, MatIconModule],
  templateUrl: './user-notebook-list.component.html',
  styleUrl: './user-notebook-list.component.scss',
})
export class UserNotebookListComponent {}
