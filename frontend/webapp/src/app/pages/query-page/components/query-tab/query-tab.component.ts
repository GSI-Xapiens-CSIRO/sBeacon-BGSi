import {
  AfterViewInit,
  Component,
  Input,
  OnDestroy,
  OnInit,
} from '@angular/core';
import {
  FormArray,
  FormBuilder,
  FormGroup,
  Validators,
  FormsModule,
  ReactiveFormsModule,
} from '@angular/forms';
import { examples } from './examples';
import { QueryService } from 'src/app/services/query.service';
import {
  parseFilters,
  parseRequestParameters,
  serializeFilters,
  serializeRequestParameters,
} from 'src/app/utils/parsers';
import { MatDialog } from '@angular/material/dialog';
import { FilterTypes, ScopeTypes } from 'src/app/utils/interfaces';
import { AuthService } from 'src/app/services/auth.service';
import { catchError, of, Subscription } from 'rxjs';
import { MatSnackBar } from '@angular/material/snack-bar';
import _ from 'lodash';
import { AsyncPipe } from '@angular/common';
import { QueryResultViewerContainerComponent } from '../query-result-viewer-container/query-result-viewer-container.component';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatInputModule } from '@angular/material/input';
import { MatOptionModule } from '@angular/material/core';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { Router, RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatCardModule } from '@angular/material/card';
import { SpinnerService } from 'src/app/services/spinner.service';
import { FilterEditorComponent } from 'src/app/components/filter-editor/filter-editor.component';
import { VariantEditorComponent } from 'src/app/components/variant-editor/variant-editor.component';
import {
  baseRangeValidator,
  acgtNValidator,
  twoRangesValidator,
} from 'src/app/utils/validators';
import { customQueries } from './custom-queries';
// import { result, query } from './test_responses/individuals';
// import { result, query } from './test_responses/biosamples';

const allowedReturns = {
  individuals: {
    biosamples: true,
    g_variants: true,
  },
  biomsaples: {
    runs: true,
    analyses: true,
    g_variants: true,
  },
  runs: {
    analyses: true,
    g_variants: true,
  },
  analyses: {
    g_variants: true,
  },
  g_variants: {
    individuals: true,
    biosamples: true,
  },
  datasets: {
    individuals: true,
    biosamples: true,
    g_variants: true,
  },
  cohorts: {
    individuals: true,
  },
};

@Component({
  selector: 'app-query-tab',
  templateUrl: './query-tab.component.html',
  styleUrl: './query-tab.component.scss',
  providers: [QueryService],
  standalone: true,
  imports: [
    MatCardModule,
    MatExpansionModule,
    MatButtonModule,
    RouterLink,
    MatIconModule,
    FormsModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatSelectModule,
    MatOptionModule,
    MatInputModule,
    MatCheckboxModule,
    MatTooltipModule,
    QueryResultViewerContainerComponent,
    AsyncPipe,
    FilterEditorComponent,
    VariantEditorComponent,
  ],
})
export class QueryTabComponent implements OnInit, AfterViewInit, OnDestroy {
  protected _ = _;
  protected allowedReturns: any = allowedReturns;
  protected loading = false;
  protected form: FormGroup;
  protected examples: any = examples;
  protected scopeTypes = ScopeTypes;
  protected filterTypes = FilterTypes;
  // TODO bug fix for https://github.com/angular/components/issues/13870
  protected disableAnimation = true;
  // displayed results
  protected results: any = null;
  protected endpoint: any = null;
  protected query: any = null;
  protected scope: any = ScopeTypes.INDIVIDUALS;
  // expansion panels
  protected openPanels: boolean[] = [false, false, false];
  // custom queries
  protected customQuery = false;
  protected customQueries: any = customQueries;
  // saved queries
  protected savedQueries: any = [];
  @Input()
  page!: number;
  private subscription: Subscription | null = null;

  ngOnInit(): void {}

  ngAfterViewInit(): void {
    // TODO bug fix for https://github.com/angular/components/issues/13870
    setTimeout(() => (this.disableAnimation = false));
  }

  ngOnDestroy(): void {
    if (this.subscription) {
      this.subscription.unsubscribe();
      this.subscription = null;
    }
  }

  constructor(
    private fb: FormBuilder,
    private qs: QueryService,
    public dg: MatDialog,
    protected auth: AuthService,
    private sb: MatSnackBar,
    private ss: SpinnerService,
  ) {
    this.form = this.fb.group({
      scope: this.fb.control(ScopeTypes.INDIVIDUALS, [Validators.required]),
      granularity: this.fb.control('count', Validators.required),
      skip: this.fb.control({ value: 0, disabled: true }, [
        Validators.required,
        Validators.min(0),
      ]),
      limit: this.fb.control({ value: 100, disabled: true }, [
        Validators.required,
        Validators.min(1),
        Validators.max(500),
      ]),
      filters: this.fb.array([], []),
      // custom return entries
      customReturn: this.fb.control(false),
      return: this.fb.control({ value: '', disabled: true }, [
        Validators.required,
      ]),
      id: this.fb.control({ value: '', disabled: true }, [Validators.required]),
      // request parameters
      requestParameters: this.fb.group(
        {
          assemblyId: this.fb.control('GRCH38', Validators.required),
          start: this.fb.control('', [
            Validators.required,
            baseRangeValidator(),
          ]),
          end: this.fb.control('', [Validators.required, baseRangeValidator()]),
          referenceName: this.fb.control('1', Validators.required),
          referenceBases: this.fb.control('N', [
            Validators.required,
            acgtNValidator(),
          ]),
          alternateBases: this.fb.control('N', [
            Validators.required,
            acgtNValidator(),
          ]),
        },
        { validators: twoRangesValidator() },
      ),
    });
    this.form.controls['requestParameters'].disable();
    this.form.controls['customReturn'].valueChanges.subscribe(
      (customReturn) => {
        if (customReturn) {
          this.form.controls['return'].enable();
          this.form.controls['id'].enable();
          this.form.markAllAsTouched();
        } else {
          this.form.controls['return'].disable();
          this.form.controls['id'].disable();
        }
      },
    );
    this.form.controls['granularity'].valueChanges.subscribe((granularity) => {
      if (granularity === 'record') {
        this.form.controls['skip'].enable();
        this.form.controls['limit'].enable();
      } else {
        this.form.controls['skip'].disable();
        this.form.controls['limit'].disable();
      }
    });
    this.form.controls['scope'].valueChanges.subscribe((scope) => {
      if (
        scope === ScopeTypes.GENOMIC_VARIANTS &&
        this.form.value.customReturn
      ) {
        this.form.controls['requestParameters'].disable();
      } else if (scope === ScopeTypes.GENOMIC_VARIANTS) {
        this.form.controls['requestParameters'].enable();
      } else {
        this.form.controls['requestParameters'].disable();
      }
    });
    this.form.controls['return'].valueChanges.subscribe((returnScope) => {
      if (returnScope === ScopeTypes.GENOMIC_VARIANTS) {
        this.form.controls['requestParameters'].enable();
      } else {
        this.form.controls['requestParameters'].disable();
      }
    });
    this.form.controls['customReturn'].valueChanges.subscribe((custom) => {
      if (this.form.value.scope === ScopeTypes.GENOMIC_VARIANTS && custom) {
        this.form.controls['requestParameters'].disable();
      } else if (this.form.value.scope === ScopeTypes.GENOMIC_VARIANTS) {
        this.form.controls['requestParameters'].enable();
      }
    });

    this.savedQueries = JSON.parse(
      localStorage.getItem('savedQueries') || '[]',
    );
  }

  openPanel(index: number) {
    this.openPanels = this.openPanels.map((o, i) =>
      index === i ? true : false,
    );
  }

  closePanel(index: number) {
    this.openPanels[index] = false;
  }

  run() {
    this.ss.start();
    const form: any = this.form.value;
    const query = {
      query: {
        filters: serializeFilters(form.filters, form.scope),
        requestedGranularity: form.granularity,
        pagination: {
          skip: form.skip,
          limit: form.limit,
        },
      },
      meta: {
        apiVersion: 'v2.0',
      },
    };
    if (
      (form.scope === ScopeTypes.GENOMIC_VARIANTS && !form.customReturn) ||
      form.return === ScopeTypes.GENOMIC_VARIANTS
    ) {
      _.set(
        query,
        'query.requestParameters',
        serializeRequestParameters(form.requestParameters),
      );
    }
    let result$;
    let endpoint: any;
    if (form.customReturn) {
      endpoint = `${form.scope}/${form.id}/${form.return}`;
      result$ = this.qs.fetch_custom(
        `${form.scope}/${form.id}/${form.return}`,
        query,
      );
    } else {
      result$ = this.qs.fetch(form.scope, query);
      endpoint = `${form.scope}/`;
    }
    result$.pipe(catchError((err, res) => of(null))).subscribe((data) => {
      if (data) {
        this.results = data;
        this.endpoint = endpoint;
        this.scope = form.customReturn ? form.return : form.scope;
      } else {
        this.sb.open(
          'API request failed. Please check your parameters.',
          'Okay',
          { duration: 60000 },
        );
      }
      this.query = query;

      this.ss.end();
    });
  }

  addFilter(filters: FormArray) {
    const group = this.fb.group({
      id: this.fb.control('', [Validators.required]),
      operator: this.fb.control({ value: '=', disabled: true }),
      includeDescendantTerms: this.fb.control(true, Validators.required),
      scope: this.fb.control(ScopeTypes.INDIVIDUALS),
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
    filters.push(group);
  }

  removeFilter(index: number) {
    (this.form.get('filters') as FormArray).removeAt(index);
  }

  reset() {
    this.customQuery = false;
    (this.form.get('filters') as FormArray).clear();

    this.form.patchValue({
      scope: ScopeTypes.INDIVIDUALS,
      granularity: 'count',
      skip: 0,
      limit: 100,
      filters: [],
      requestParameters: {
        assemblyId: 'GRCH38',
        start: '',
        end: '',
        referenceName: '1',
        referenceBases: 'N',
        alternateBases: 'N',
      },
      customReturn: false,
      id: '',
      return: ScopeTypes.INDIVIDUALS,
    });
    this.results = null;
    this.query = null;
    this.endpoint = null;
    this.scope = null;
  }

  runCustomQuery(query: any) {
    query.func(this);
  }

  loadExample(query: any) {
    this.reset();
    (this.form.get('filters') as FormArray).clear();
    _.range(query.body.query.filters.length).forEach(() => {
      this.addFilter(this.form.get('filters') as FormArray);
    });

    this.form.patchValue({
      scope: query.scope,
      granularity: query.body.query.requestedGranularity,
      id: query.id,
      return: query.return,
      customReturn: query.customReturn,
      skip: query.body.query.pagination.skip,
      limit: query.body.query.pagination.limit,
      filters: parseFilters(query.body.query.filters, query.scope),
    });

    if (query.scope === ScopeTypes.GENOMIC_VARIANTS && !query.customReturn) {
      this.form.patchValue({
        requestParameters: parseRequestParameters(
          query.body.query.requestParameters,
        ),
      });
    }
  }

  async saveQuery() {
    const { SaveQueryDialogComponent } = await import(
      'src/app/pages/query-page/components/save-query-dialog/save-query-dialog.component'
    );
    const dialog = this.dg.open(SaveQueryDialogComponent, {
      data: {},
    });

    dialog.afterClosed().subscribe((text) => {
      if (_.isEmpty(text)) {
        return;
      }
      const saved = JSON.parse(localStorage.getItem('savedQueries') || '[]');
      const form: any = this.form.value;
      const entry = {
        text: text,
        scope: form.scope,
        return: form.return,
        id: form.id,
        customReturn: form.customReturn,
        body: {
          query: {
            filters: serializeFilters(form.filters, form.scope),
            requestedGranularity: form.granularity,
            pagination: {
              skip: form.skip,
              limit: form.limit,
            },
          },
          meta: {
            apiVersion: 'v2.0',
          },
        },
      };
      if (form.scope === ScopeTypes.GENOMIC_VARIANTS && !form.customReturn) {
        _.set(
          entry,
          'body.query.requestParameters',
          serializeRequestParameters(form.requestParameters),
        );
      }
      console.log(entry);
      this.savedQueries = [...saved, entry];
      localStorage.setItem('savedQueries', JSON.stringify(this.savedQueries));
    });
  }

  async deleteSavedQuery(index: number) {
    const { ActionConfirmationDialogComponent } = await import(
      'src/app/components/action-confirmation-dialog/action-confirmation-dialog.component'
    );
    const dialog = this.dg.open(ActionConfirmationDialogComponent, {
      data: {
        title: 'Delete Saved Query',
        message: 'Are you sure you want to delete this saved query?',
      },
    });

    dialog.afterClosed().subscribe((yes) => {
      if (yes) {
        const saved = JSON.parse(localStorage.getItem('savedQueries') || '[]');
        this.savedQueries = _.filter(saved, (_, idx: number) => idx !== index);
        localStorage.setItem('savedQueries', JSON.stringify(this.savedQueries));
      }
    });
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
        (this.form.get('filters') as FormArray).removeAt(index);
        const original = (this.form.get('filters') as FormArray).value;
        const parsed = parseFilters(filters, scope);
        original.splice(index, 0, ...parsed);
        const combined = original;

        (this.form.get('filters') as FormArray).clear();
        _.range(combined.length).forEach(() => {
          this.addFilter(this.form.get('filters') as FormArray);
        });

        this.form.patchValue({
          filters: parseFilters(combined, scope),
        });
      }
    });
  }

  async searchEntries() {
    const scope = this.form.value.scope;

    if (scope === ScopeTypes.GENOMIC_VARIANTS) {
      alert(
        'This is not implemented yet! Requires special iterator for variants, probably a new dialog box',
      );
      return;
    }
    const { EntryIdSelectionDialogComponent } = await import(
      'src/app/components/entry-id-selection-dialog/entry-id-selection-dialog.component'
    );
    const dialog = this.dg.open(EntryIdSelectionDialogComponent, {
      data: { scope },
    });

    dialog.afterClosed().subscribe((entry) => {
      if (entry) {
        this.form.patchValue({
          id: entry,
        });
      }
    });
  }
}
