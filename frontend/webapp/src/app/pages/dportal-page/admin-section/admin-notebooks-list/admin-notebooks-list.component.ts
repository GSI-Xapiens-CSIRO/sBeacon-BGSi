import { Component, ViewChildren } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatOptionModule } from '@angular/material/core';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { DportalService } from 'src/app/services/dportal.service';
import { catchError, of } from 'rxjs';
import { AdminNotebookItemComponent } from './admin-notebook-item/admin-notebook-item.component';

export interface InstanceInfo {
  instanceName: string;
  userFirstName: string;
  userLastName: string;
  userEmail: string;
  status: string;
  volumeSize: number;
  instanceType: string;
}

@Component({
  selector: 'app-notebooks',
  standalone: true,
  imports: [
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatSelectModule,
    MatOptionModule,
    AdminNotebookItemComponent,
  ],
  templateUrl: './admin-notebooks-list.component.html',
  styleUrl: './admin-notebooks-list.component.scss',
})
export class NotebooksComponent {
  @ViewChildren('notebook') notebookItems?: AdminNotebookItemComponent[];
  notebooks: InstanceInfo[] = [];
  loading = false;

  constructor(private dps: DportalService) {}

  ngOnInit(): void {
    this.list();
  }

  list() {
    this.notebookItems?.map((n) => n.getStatus());
    this.loading = true;
    this.dps
      .getAdminNotebooks()
      .pipe(catchError(() => of(null)))
      .subscribe((notebooks: InstanceInfo[]) => {
        if (notebooks) {
          this.notebooks = notebooks;
        }
        this.loading = false;
      });
  }

  remove(notebook: string) {
    this.notebooks = this.notebooks.filter((n) => n.instanceName !== notebook);
  }
}
