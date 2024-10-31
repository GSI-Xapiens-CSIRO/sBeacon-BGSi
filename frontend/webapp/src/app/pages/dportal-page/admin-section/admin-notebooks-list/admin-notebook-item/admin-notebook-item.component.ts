import {
  Component,
  EventEmitter,
  Input,
  OnChanges,
  Output,
  SimpleChanges,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { DportalService } from 'src/app/services/dportal.service';
import { InstanceInfo } from '../admin-notebooks-list.component';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { catchError, of } from 'rxjs';

export enum Status {
  PENDING = 'Pending',
  IN_SERVICE = 'InService',
  STOPPING = 'Stopping',
  STOPPED = 'Stopped',
  FAILED = 'Failed',
  DELETING = 'Deleting',
  UPDATING = 'Updating',
}

@Component({
  selector: 'app-admin-notebook-item',
  standalone: true,
  imports: [MatButtonModule, MatIconModule, MatDialogModule],
  templateUrl: './admin-notebook-item.component.html',
  styleUrl: './admin-notebook-item.component.scss',
})
export class AdminNotebookItemComponent implements OnChanges {
  @Input({ required: true }) notebook!: InstanceInfo;
  @Output() deleted = new EventEmitter<void>();
  Status = Status;
  cachedStatus: InstanceInfo | null = null;

  constructor(
    private dps: DportalService,
    private dg: MatDialog,
  ) {}

  ngOnChanges(changes: SimpleChanges): void {
    // cache the initial status
    if (changes['notebook'].firstChange) {
      this.cachedStatus = changes['notebook'].currentValue;
    }
  }

  public getStatus() {
    this.dps
      .getAdminNotebookStatus(this.notebook.instanceName)
      .subscribe((res) => {
        // merge res to the cached status
        if (this.cachedStatus) {
          this.cachedStatus = { ...this.cachedStatus, ...res };
        }
      });
  }

  async stop() {
    const { ActionConfirmationDialogComponent } = await import(
      '../../../../../components/action-confirmation-dialog/action-confirmation-dialog.component'
    );

    const dialog = this.dg.open(ActionConfirmationDialogComponent, {
      data: {
        title: 'Stop Notebook',
        message: 'Are you sure you want to stop this notebook?',
      },
    });
    dialog.afterClosed().subscribe((result) => {
      if (result) {
        this.dps.stopAdminNotebook(this.notebook.instanceName).subscribe(() => {
          this.getStatus();
        });
      }
    });
  }

  async delete() {
    const { ActionConfirmationDialogComponent } = await import(
      '../../../../../components/action-confirmation-dialog/action-confirmation-dialog.component'
    );

    const dialog = this.dg.open(ActionConfirmationDialogComponent, {
      data: {
        title: 'Delete Notebook',
        message: 'Are you sure you want to delete this notebook?',
      },
    });
    dialog.afterClosed().subscribe((result) => {
      if (result) {
        this.dps
          .deleteAdminNotebook(this.notebook.instanceName)
          .pipe(catchError(() => of(null)))
          .subscribe(() => {
            this.deleted.emit();
          });
      }
    });
  }
}
