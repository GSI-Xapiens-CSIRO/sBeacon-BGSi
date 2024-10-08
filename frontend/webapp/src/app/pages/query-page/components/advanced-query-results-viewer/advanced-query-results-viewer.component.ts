import { Component, Input, OnChanges } from '@angular/core';
import {
  FormArray,
  FormBuilder,
  FormGroup,
  Validators,
  FormsModule,
  ReactiveFormsModule,
} from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Subject, catchError, forkJoin, map, of, takeUntil } from 'rxjs';
import { QueryService } from 'src/app/services/query.service';
import { FilterTypes, ScopeTypes } from 'src/app/utils/interfaces';
import { parseFilters, serializeFilters } from 'src/app/utils/parsers';
import { TermFreqPlotComponent } from '../term-freq-plot/term-freq-plot.component';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { RouterLink } from '@angular/router';
import { MatInputModule } from '@angular/material/input';
import { MatOptionModule } from '@angular/material/core';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatCardModule } from '@angular/material/card';
import { FilterEditorComponent } from 'src/app/components/filter-editor/filter-editor.component';
import _ from 'lodash';

@Component({
  selector: 'app-advanced-query-results-viewer',
  templateUrl: './advanced-query-results-viewer.component.html',
  styleUrl: './advanced-query-results-viewer.component.scss',
  standalone: true,
  imports: [
    MatCardModule,
    FormsModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatSelectModule,
    MatOptionModule,
    MatInputModule,
    RouterLink,
    MatCheckboxModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    TermFreqPlotComponent,
    FilterEditorComponent,
  ],
})
export class AdvancedQueryResultsViewerComponent implements OnChanges {
  @Input({ required: true })
  public query: any;
  @Input({ required: true })
  public scope: any;
  @Input({ required: true })
  public endpoint: any;
  @Input({ required: true })
  public words: any;
  @Input({ required: true })
  public results: any;
  protected filtersForm: FormArray;
  protected scopeTypes = ScopeTypes;
  protected filterTypes = FilterTypes;
  protected loading = false;
  protected show = false;
  protected completed = 0;
  protected uniqueWords: any[] = [];
  protected terms: any = [];
  protected counts: any[] = [];
  protected _ = _;
  private destroy$ = new Subject<void>();

  constructor(
    private fb: FormBuilder,
    private dg: MatDialog,
    private qs: QueryService,
    private sb: MatSnackBar,
  ) {
    this.filtersForm = this.fb.array(
      [],
      [Validators.required, Validators.minLength(1)],
    );
  }

  ngOnChanges(): void {
    this.uniqueWords = _.filter(
      _.uniqBy(this.words, (word: any) => word.id),
      (word) =>
        _.isEmpty(
          _.find(this.query.query.filters, (filter) => word.id === filter.id),
        ),
    );
    this.reset();
  }

  addFilter(id = '') {
    const group = this.fb.group({
      id: this.fb.control(id, [Validators.required]),
      operator: this.fb.control({ value: '=', disabled: true }),
      includeDescendantTerms: this.fb.control(true, Validators.required),
      scope: this.fb.control(this.scope),
      type: this.fb.control(FilterTypes.ONTOLOGY),
      value: this.fb.control({ value: '', disabled: true }, [
        Validators.required,
      ]),
    });
    group.controls['type'].valueChanges.subscribe((filter) => {
      if (filter !== FilterTypes.ALPHANUMERIC) {
        group.controls['value'].disable();
        group.controls['operator'].disable();
      } else {
        group.controls['value'].enable();
        group.controls['operator'].enable();
      }
      if (filter !== FilterTypes.ONTOLOGY) {
        group.controls['includeDescendantTerms'].disable();
      } else {
        group.controls['includeDescendantTerms'].enable();
      }
    });
    group.markAllAsTouched();
    this.filtersForm.push(group);
  }

  removeFilter(index: number) {
    this.filtersForm.removeAt(index);
  }

  async searchFilters(filter: FormGroup, index: number) {
    const scope = filter.get('scope')!.value;
    const type = filter.get('type')!.value;
    const { FilterSelectionDialogComponent } = await import(
      'src/app/components/filter-selection-dialog/filter-selection-dialog.component'
    );
    const dialog = this.dg.open(FilterSelectionDialogComponent, {
      data: { scope, type },
    });

    dialog.afterClosed().subscribe((filters) => {
      if (!_.isEmpty(filters)) {
        this.filtersForm.removeAt(index);
        const original = this.filtersForm.value;
        const parsed = parseFilters(filters, scope);
        original.splice(index, 0, ...parsed);
        const combined = original;

        this.filtersForm.clear();
        _.range(combined.length).forEach(() => {
          this.addFilter();
        });

        this.filtersForm.patchValue(parseFilters(combined, scope));
      }
    });
  }

  async run() {
    this.loading = true;
    this.completed = 0;
    this.terms = _.uniqWith(
      this.filtersForm.value,
      (arrVal: any, othVal: any) =>
        arrVal.id === othVal.id && arrVal.type === othVal.type,
    );

    const observables$ = _.map(this.terms, (filter) => {
      const newQuery = _.cloneDeep(this.query);
      newQuery.query.requestedGranularity = 'count';
      newQuery.query.filters = _.uniqWith(
        [
          ...this.query.query.filters,
          ...serializeFilters([filter], this.scope),
        ],
        (arrVal: any, othVal: any) =>
          arrVal.id === othVal.id && arrVal.type === othVal.type,
      );
      return this.qs.fetch_custom(this.endpoint, newQuery).pipe(
        map((response) => {
          this.completed++;
          return {
            id: filter.id,
            // TODO the label must be fetched from elsewhere
            // because the filter may be one that is not already seen in query/result
            label: '',
            count: _.get(response, 'responseSummary.numTotalResults', 0),
          };
        }),
      );
    });

    forkJoin(observables$)
      .pipe(
        takeUntil(this.destroy$),
        catchError((_) => of(null)),
      )
      .subscribe((counts) => {
        if (!counts) {
          this.sb.open('Unable to fetch details', 'Okay', { duration: 60000 });
        } else if (counts.length == this.terms.length) {
          this.counts = _.reverse(_.sortBy(counts, (item) => item.count));
        }
        this.loading = false;
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  reset() {
    this.filtersForm.clear();
    this.terms = [];
    this.counts = [];
    this.completed = 0;
  }

  async openTermPicker() {
    const { TermPickerDialogComponent } = await import(
      '../term-picker-dialog/term-picker-dialog.component'
    );
    const dialog = this.dg.open(TermPickerDialogComponent, {
      data: {
        terms: this.uniqueWords,
        selected: this.filtersForm.value
          .filter((group: any) => group.type === FilterTypes.ONTOLOGY)
          .map((group: any) => group.id),
      },
    });

    dialog.afterClosed().subscribe((selected) => {
      if (_.isEmpty(selected)) return;
      selected.forEach((word: any) => {
        if (
          _.isEmpty(
            _.find(
              this.filtersForm.value,
              (group: any) =>
                group.type === FilterTypes.ONTOLOGY && group.id === word,
            ),
          )
        ) {
          this.addFilter(word);
        }
      });
    });
  }
}
