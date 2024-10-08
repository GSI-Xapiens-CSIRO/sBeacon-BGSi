import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import * as _ from 'lodash';
import { ScopeTypes } from 'src/app/utils/interfaces';
import { TimeSeriesPlotComponent } from '../time-series-plot/time-series-plot.component';
import { TermFreqPlotComponent } from '../term-freq-plot/term-freq-plot.component';
import { WordCloudPlotComponent } from '../word-cloud-plot/word-cloud-plot.component';
import { MatCardModule } from '@angular/material/card';

@Component({
  selector: 'app-visual-query-results-viewer',
  templateUrl: './visual-query-results-viewer.component.html',
  styleUrl: './visual-query-results-viewer.component.scss',
  standalone: true,
  imports: [
    MatCardModule,
    WordCloudPlotComponent,
    TermFreqPlotComponent,
    TimeSeriesPlotComponent,
  ],
})
export class VisualQueryResultsViewerComponent implements OnChanges {
  @Input({ required: true }) words: any;
  @Input({ required: true }) results: any;
  @Input({ required: true }) scope: any;
  protected counts: any[] = [];
  protected ScopeTypes = ScopeTypes;
  protected _ = _;

  ngOnChanges(): void {
    const counts = _.countBy(this.words, (word: any) => word.id);
    this.counts = _.map(
      _.uniqBy(this.words, (word: any) => word.id),
      (word: any) => ({
        id: word.id,
        label: word.label,
        count: counts[word.id],
      }),
    );
    this.counts.sort((b: any, a: any) => {
      return a.count - b.count;
    });
  }
}
