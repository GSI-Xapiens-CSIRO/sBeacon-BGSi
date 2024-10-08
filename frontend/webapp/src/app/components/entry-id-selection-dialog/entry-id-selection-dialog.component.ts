import {
  ChangeDetectorRef,
  Component,
  Inject,
  Injectable,
  ViewChild,
} from '@angular/core';
import {
  MatCheckboxChange,
  MatCheckboxModule,
} from '@angular/material/checkbox';
import {
  MAT_DIALOG_DATA,
  MatDialogModule,
  MatDialogRef,
} from '@angular/material/dialog';
import {
  MatPaginator,
  MatPaginatorIntl,
  MatPaginatorModule,
} from '@angular/material/paginator';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { Subject, catchError, from, map, of, startWith, switchMap } from 'rxjs';
import { QueryService } from 'src/app/services/query.service';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { NgxJsonViewerModule } from 'ngx-json-viewer';

import { MatButtonModule } from '@angular/material/button';
import * as _ from 'lodash';
import { ComponentSpinnerComponent } from '../component-spinner/component-spinner.component';

@Component({
  selector: 'app-entry-id-selection-dialog',
  templateUrl: './entry-id-selection-dialog.component.html',
  styleUrls: ['./entry-id-selection-dialog.component.scss'],
  providers: [QueryService],
  standalone: true,
  imports: [
    CommonModule,
    MatCheckboxModule,
    MatCardModule,
    NgxJsonViewerModule,
    MatPaginatorModule,
    MatDialogModule,
    MatTableModule,
    MatButtonModule,
    ComponentSpinnerComponent,
  ],
})
export class EntryIdSelectionDialogComponent {
  @ViewChild('paginator')
  paginator!: MatPaginator;

  protected _ = _;
  protected loading = false;
  protected skip = 0;
  protected limit = 0;
  protected total = 0;
  protected entries: any = [];
  protected dataSourceEntries = new MatTableDataSource<any>([]);
  protected displayedColumnsEntries: string[] = [];
  protected selected: string | null = null;

  constructor(
    public dialogRef: MatDialogRef<EntryIdSelectionDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private qs: QueryService,
    private cd: ChangeDetectorRef,
  ) {}

  ngAfterViewInit(): void {
    this.paginator.page
      .pipe(
        startWith({}),
        switchMap(() => {
          this.loading = true;
          this.cd.detectChanges();
          this.limit = this.paginator.pageSize;
          return this.qs
            .fetch(this.data.scope, {
              query: {
                filters: [],
                requestedGranularity: 'record',
                pagination: {
                  skip: this.limit * this.paginator.pageIndex,
                  limit: this.limit,
                },
              },
              meta: {
                apiVersion: 'v2.0',
              },
            })
            .pipe(catchError(() => of(null)));
        }),
        map((data) => {
          // Flip flag to show that loading has finished.
          this.total = _.get(data, 'responseSummary.numTotalResults');
          this.loading = false;
          this.cd.detectChanges();
          if (data === null) {
            return [];
          }
          return data;
        }),
      )
      .subscribe((results) => {
        const resultsArray = _.isEmpty(results.response.resultSets)
          ? results.response.collections
          : results.response.resultSets[0].results;

        if (this.entries.length && _.isEmpty(resultsArray)) {
          this.paginator.pageIndex -= 1;
          console.log('page out of bounds');
        } else {
          const idName = _.isEmpty(resultsArray[0]['id'])
            ? 'variantInternalId'
            : 'id';
          this.displayedColumnsEntries = [
            'selected',
            idName,
            ..._.filter(_.keys(resultsArray[0]), (item) => item != idName),
          ];
          this.entries = resultsArray;
        }
      });
  }

  cancel(): void {
    this.dialogRef.close(null);
  }

  done(): void {
    this.dialogRef.close(this.selected);
  }

  select(entry: any, event: MatCheckboxChange) {
    if (event.checked) {
      this.selected = entry.id;
    } else {
      this.selected = null;
    }
  }
}
