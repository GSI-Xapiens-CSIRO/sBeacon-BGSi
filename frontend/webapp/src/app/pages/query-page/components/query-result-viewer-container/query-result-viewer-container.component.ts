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

@Component({
  selector: 'app-query-result-viewer-container',
  templateUrl: './query-result-viewer-container.component.html',
  styleUrls: ['./query-result-viewer-container.component.scss'],
  standalone: true,
  imports: [
    MatCardModule,
    MatTabsModule,
    VisualQueryResultsViewerComponent,
    AdvancedQueryResultsViewerComponent,
    TabularQueryResultsViewerComponent,
    TextQueryResultsViewerComponent,
    MatButtonModule,
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
}
