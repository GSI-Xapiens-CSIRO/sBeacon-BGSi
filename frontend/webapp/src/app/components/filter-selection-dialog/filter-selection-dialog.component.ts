import {
  AfterViewInit,
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
import { Subject, catchError, map, of, startWith, switchMap } from 'rxjs';
import { FilterService } from 'src/app/services/filter.service';
import * as _ from 'lodash';
import { MatSnackBar } from '@angular/material/snack-bar';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { NgxJsonViewerModule } from 'ngx-json-viewer';

import { MatButtonModule } from '@angular/material/button';
import { ComponentSpinnerComponent } from '../component-spinner/component-spinner.component';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

// Docs: https://material.angular.io/components/paginator/examples
// Paginator internationalization
@Injectable()
export class MyCustomPaginatorIntl implements MatPaginatorIntl {
  changes = new Subject<void>();

  // For internationalization, the `$localize` function from
  // the `@angular/localize` package can be used.
  firstPageLabel = $localize`First page`;
  itemsPerPageLabel = $localize`Items per page:`;
  lastPageLabel = $localize`Last page`;

  // You can set labels to an arbitrary string too, or dynamically compute
  // it through other third-party internationalization libraries.
  nextPageLabel = 'Next page';
  previousPageLabel = 'Previous page';

  getRangeLabel(page: number, pageSize: number, length: number): string {
    return $localize`Page ${page + 1}`;
  }
}

@Component({
  selector: 'app-filter-selection-dialog',
  templateUrl: './filter-selection-dialog.component.html',
  styleUrls: ['./filter-selection-dialog.component.scss'],
  providers: [
    { provide: MatPaginatorIntl, useClass: MyCustomPaginatorIntl },
    FilterService,
  ],
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
    MatFormFieldModule,
    MatInputModule,
  ],
})
export class FilterSelectionDialogComponent implements AfterViewInit {
  @ViewChild('paginatorFilters') paginatorFilters!: MatPaginator;
  protected _ = _;
  protected loading = false;
  protected skip = 0;
  protected limit = 5;
  protected total = 999;
  protected dataSourceFilters = new MatTableDataSource<any>([]);
  protected displayedColumnsFilters = ['selected', 'id', 'label', 'type'];
  protected selected: { [key: string]: any } = {};
  protected filter = '';

  constructor(
    public dialogRef: MatDialogRef<FilterSelectionDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private fs: FilterService,
    private cd: ChangeDetectorRef,
    private sb: MatSnackBar,
  ) {}

  ngAfterViewInit(): void {
    this.paginatorFilters.page
      .pipe(
        startWith({}),
        switchMap(() => {
          this.loading = true;
          this.cd.detectChanges();
          this.limit = this.paginatorFilters.pageSize;
          return this.fs
            .fetch_by_scope(this.data.scope, {
              skip: this.limit * this.paginatorFilters.pageIndex,
              limit: this.limit,
            })
            .pipe(catchError(() => of(null)));
        }),
        map((data) => {
          this.loading = false;
          this.cd.detectChanges();
          this.total = 999;
          return data;
        }),
      )
      .subscribe((results) => {
        if (!results) {
          this.sb.open('API request failed', 'Okay', { duration: 60000 });
          return;
        }
        if (
          this.dataSourceFilters.data.length &&
          _.isEmpty(_.get(results, 'response.filteringTerms', []))
        ) {
          this.paginatorFilters.pageIndex -= 1;
          console.log('page out of bounds');
        } else {
          this.dataSourceFilters = new MatTableDataSource(
            _.get(results, 'response.filteringTerms', []),
          );
          this.dataSourceFilters.filter = this.filter;
        }
      });
  }

  cancel(): void {
    this.dialogRef.close([]);
  }

  done(): void {
    this.dialogRef.close(_.map(this.selected, (v, _) => v));
  }

  select(filter: any, event: MatCheckboxChange) {
    if (event.checked) {
      _.set(this.selected, filter.id, filter);
    } else {
      _.unset(this.selected, filter.id);
    }
  }

  applyFilter(event: Event) {
    this.filter = (event.target as HTMLInputElement).value.trim().toLowerCase();
    this.dataSourceFilters.filter = this.filter;
  }
}
