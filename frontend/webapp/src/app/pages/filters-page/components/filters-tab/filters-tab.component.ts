import { Component } from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  Validators,
  FormsModule,
  ReactiveFormsModule,
} from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { catchError, of } from 'rxjs';
import { FilterService } from 'src/app/services/filter.service';
import { ScopeTypes } from 'src/app/utils/interfaces';
import { environment } from 'src/environments/environment';
import * as _ from 'lodash';
import { GlobalSpinnerComponent } from '../../../../components/global-spinner/global-spinner.component';
import { FiltersResultViewerComponent } from '../../components/filters-result-viewer/filters-result-viewer.component';
import { TermFreqViewerComponent } from '../../components/term-freq-viewer/term-freq-viewer.component';
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { RouterLink } from '@angular/router';
import { MatInputModule } from '@angular/material/input';
import { MatOptionModule } from '@angular/material/core';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatCardModule } from '@angular/material/card';
import { SpinnerService } from 'src/app/services/spinner.service';
// import { result, testTerms } from './test_responses/filters';

@Component({
  selector: 'app-filters-tab',
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
    TermFreqViewerComponent,
    FiltersResultViewerComponent,
  ],
  providers: [FilterService],
  templateUrl: './filters-tab.component.html',
  styleUrl: './filters-tab.component.scss',
})
export class FiltersTabComponent {
  protected _ = _;
  protected form: FormGroup;
  protected query: any = null;
  protected endpoint: any = null;
  protected results: any = null;
  protected scopeTypes = ScopeTypes;
  protected activeScope: string | null = null;
  protected terms: any[] = [];

  constructor(
    private fb: FormBuilder,
    private fs: FilterService,
    private dg: MatDialog,
    private sb: MatSnackBar,
    private ss: SpinnerService,
  ) {
    this.form = fb.group({
      scope: this.fb.control(ScopeTypes.INDIVIDUALS, [Validators.required]),
      id: this.fb.control({ value: '', disabled: true }, [Validators.required]),
      skip: this.fb.control(0, [Validators.required, Validators.min(0)]),
      limit: this.fb.control(100, [
        Validators.required,
        Validators.min(1),
        Validators.max(500),
      ]),
      stats: this.fb.control(false),
    });

    this.form.controls['scope'].valueChanges.subscribe((scope) => {
      if (scope === ScopeTypes.DATASETS || scope == ScopeTypes.COHORTS) {
        this.form.controls['id'].enable();
        this.form.controls['id'].markAsTouched();
        this.form.controls['stats'].setValue(false);
        this.form.controls['stats'].disable();
      } else {
        this.form.controls['stats'].enable();
        this.form.controls['id'].disable();
      }
    });
  }

  run() {
    this.ss.start();
    const form = this.form.value;
    const query = {
      skip: form.skip,
      limit: form.limit,
    };
    let result$;
    let endpoint: any;

    if (
      form.scope === ScopeTypes.DATASETS ||
      form.scope == ScopeTypes.COHORTS
    ) {
      result$ = this.fs.fetch_by_scope_and_id(form.scope, form.id, query);
      endpoint = `${environment.api_endpoint_sbeacon.endpoint}${form.scope}/${form.id}/filtering_terms`;
    } else {
      result$ = this.fs.fetch_by_scope(form.scope, query);
      endpoint = `${environment.api_endpoint_sbeacon.endpoint}${form.scope}/filtering_terms`;
    }

    result$.pipe(catchError((err) => of(null))).subscribe((data) => {
      if (data) {
        this.results = data;
        this.endpoint = endpoint;
        this.terms = form.stats
          ? _.map(_.get(data, 'response.filteringTerms'), (term) => ({
              id: term.id,
              label: term.label,
            }))
          : [];
        this.activeScope = form.stats ? form.scope : null;
      } else {
        if (!data) {
          this.sb.open('API request failed', 'Okay', { duration: 60000 });
          return;
        }
      }
      this.ss.end();
      this.query = query;
    });
  }

  reset() {
    this.results = null;
    this.query = null;
    this.endpoint = null;
    this.terms = [];
    this.activeScope = null;
    this.form.patchValue({
      scope: ScopeTypes.INDIVIDUALS,
      skip: 0,
      limit: 100,
    });
  }

  async searchIds() {
    const scope = this.form.value.scope;
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
