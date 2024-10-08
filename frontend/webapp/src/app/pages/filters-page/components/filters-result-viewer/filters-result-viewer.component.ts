import {
  AfterViewInit,
  ChangeDetectorRef,
  Component,
  Input,
  OnChanges,
  SimpleChanges,
  ViewChild,
} from '@angular/core';
import { MatPaginator, MatPaginatorModule } from '@angular/material/paginator';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import * as _ from 'lodash';
import { MatButtonModule } from '@angular/material/button';
import { NgxJsonViewerModule } from 'ngx-json-viewer';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatTabsModule } from '@angular/material/tabs';
import { MatCardModule } from '@angular/material/card';
import { ClipboardModule } from '@angular/cdk/clipboard';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';

@Component({
  selector: 'app-filters-result-viewer',
  templateUrl: './filters-result-viewer.component.html',
  styleUrls: ['./filters-result-viewer.component.scss'],
  standalone: true,
  imports: [
    MatCardModule,
    MatTabsModule,
    MatTableModule,
    MatPaginatorModule,
    MatFormFieldModule,
    MatInputModule,
    MatExpansionModule,
    NgxJsonViewerModule,
    MatButtonModule,
    ClipboardModule,
    MatIconModule,
    MatTooltipModule,
  ],
})
export class FiltersResultViewerComponent implements OnChanges, AfterViewInit {
  @Input() results: any;
  @Input() endpoint: any;
  @Input() query: any;
  @ViewChild('paginatorResources') protected paginatorResoureces!: MatPaginator;
  @ViewChild('paginatorFilters') protected paginatorFilters!: MatPaginator;

  protected _ = _;
  // expanders start
  protected queryJSONOpen = false;
  protected metaJSONOpen = false;
  protected responseJSONOpen = false;
  protected fullJSONOpen = false;
  protected tableResourcesOpen = false;
  protected tableFiltersOpen = false;
  // expanders end
  protected displayedColumnsResources: string[] = [];
  protected displayedColumnsFilters: string[] = [];
  protected dataSourceResources = new MatTableDataSource<any>([]);
  protected dataSourceFilters = new MatTableDataSource<any>([]);
  protected resourceExists = false;
  protected filtersExists = false;

  constructor(private cd: ChangeDetectorRef) {}

  ngOnChanges(): void {
    this.filtersExists = this.results.response.filteringTerms.length > 0;
    this.resourceExists = this.results.response.resources.length > 0;
    // at this point without cd, viewchild fails
    this.cd.detectChanges();
    this.processRecords();
  }

  processRecords() {
    const resources = this.results.response.resources;
    const filters = this.results.response.filteringTerms;
    const headerResources = [
      'id',
      ..._.filter(_.keys(resources[0]), (item) => item != 'id'),
    ];
    const headerFilters = [
      'id',
      ..._.filter(_.keys(filters[0]), (item) => item != 'id'),
    ];
    const dataResources = _.map(resources, (item) =>
      _.pick(item, headerResources),
    );
    const dataFilters = _.map(filters, (item) => _.pick(item, headerFilters));

    this.displayedColumnsResources = headerResources;
    this.displayedColumnsFilters = headerFilters;
    this.dataSourceResources = new MatTableDataSource<any>(dataResources);
    this.dataSourceFilters = new MatTableDataSource<any>(dataFilters);
    this.dataSourceResources.paginator = this.paginatorResoureces;
    this.dataSourceFilters.paginator = this.paginatorFilters;
  }

  ngAfterViewInit(): void {
    this.dataSourceResources.paginator = this.paginatorResoureces;
    this.dataSourceFilters.paginator = this.paginatorFilters;
  }

  download(data: any) {
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: 'text/json;charset=utf-8;',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'data.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  applyFilter(event: Event) {
    const filterValue = (event.target as HTMLInputElement).value;
    this.dataSourceFilters.filter = filterValue.trim().toLowerCase();
  }
}
