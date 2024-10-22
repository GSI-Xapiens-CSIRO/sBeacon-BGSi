import { Component, Input, OnChanges } from '@angular/core';
import { extract_terms } from 'src/app/utils/onto';
import * as _ from 'lodash';
import { MatButtonModule } from '@angular/material/button';
import { TextQueryResultsViewerComponent } from '../text-query-results-viewer/text-query-results-viewer.component';
import { TabularQueryResultsViewerComponent } from '../tabular-query-results-viewer/tabular-query-results-viewer.component';
import { AdvancedQueryResultsViewerComponent } from '../advanced-query-results-viewer/advanced-query-results-viewer.component';
import { VisualQueryResultsViewerComponent } from '../visual-query-results-viewer/visual-query-results-viewer.component';
import { MatTabsModule } from '@angular/material/tabs';
import { MatCardModule } from '@angular/material/card';
import { DportalService } from 'src/app/services/dportal.service';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { SpinnerService } from 'src/app/services/spinner.service';
import { catchError, from, of } from 'rxjs';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { Storage } from 'aws-amplify';

@Component({
  selector: 'app-query-result-viewer-container',
  templateUrl: './query-result-viewer-container.component.html',
  styleUrls: ['./query-result-viewer-container.component.scss'],
  standalone: true,
  imports: [
    MatCardModule,
    MatTabsModule,
    MatDialogModule,
    VisualQueryResultsViewerComponent,
    AdvancedQueryResultsViewerComponent,
    TabularQueryResultsViewerComponent,
    TextQueryResultsViewerComponent,
    MatButtonModule,
    MatSnackBarModule,
  ],
})
export class QueryResultViewerContainerComponent implements OnChanges {
  @Input()
  results: any;
  @Input()
  endpoint: any;
  @Input()
  query: any;
  @Input()
  scope: any;

  protected _ = _;
  protected granularity = '';
  protected exists = false;
  protected words: any[] = [];

  constructor(
    private dg: MatDialog,
    private ss: SpinnerService,
    private sb: MatSnackBar,
  ) {}

  ngOnChanges(): void {
    this.granularity = this.results.meta.returnedGranularity;
    this.exists = this.results.responseSummary.exists;
    this.words = [
      ...extract_terms(
        _.get(this.results, 'response.resultSets[0].results', []),
      ),
      ...extract_terms(_.get(this.results, 'response.collections', [])),
    ];
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

  async save(content: any) {
    const { TextInputDialogComponent } = await import(
      '../../../../components/text-input-dialog/text-input-dialog.component'
    );

    const dialog = this.dg.open(TextInputDialogComponent, {
      data: {
        title: 'Save Query Results',
        message:
          'Please enter a name for the file. Dupliactions will be overwritten.',
        label: 'Name your data',
        placeholder: 'My query results',
      },
    });
    dialog.afterClosed().subscribe((name) => {
      if (name) {
        this.ss.start();
        from(
          Storage.put(`saved-queries/${name}.json`, content, {
            level: 'private',
            contentType: 'application/json',
          }),
        )
          .pipe(catchError(() => of(null)))
          .subscribe((res) => {
            if (!res) {
              this.sb.open('Saving failed', 'Okay', { duration: 60000 });
            }
            this.ss.end();
          });
      }
    });
  }
}
