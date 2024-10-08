import {
  Component,
  ElementRef,
  Input,
  OnChanges,
  OnDestroy,
  SimpleChanges,
  ViewChild,
} from '@angular/core';
import * as _ from 'lodash';
import { PlotlyComponent, PlotlyModule } from 'angular-plotly.js';
import * as PlotlyJS from 'plotly.js-dist-min';
import { extract_terms } from 'src/app/utils/onto';
import { MatDialog } from '@angular/material/dialog';

PlotlyModule.plotlyjs = PlotlyJS;

@Component({
  selector: 'app-time-series-plot',
  templateUrl: './time-series-plot.component.html',
  styleUrl: './time-series-plot.component.scss',
  standalone: true,
  imports: [PlotlyModule],
})
export class TimeSeriesPlotComponent implements OnChanges, OnDestroy {
  @Input({ required: true }) results: any;
  @ViewChild('figure') protected figure!: PlotlyComponent;
  protected data: any = [];
  protected terms: any = [];
  protected visibleTerms: string[] = [];
  protected layout = {
    xaxis: {
      title: 'Year and Month',
      ticklabeloverflow: 'allow',
      type: 'date',
      tickformat: '%b-%Y',
      automargin: true,
      dtick: 'M1',
      autorange: true,
      rangeslider: {
        thickness: 0.3,
      },
    },
    yaxis: {
      title: 'Frequency of ontology terms',
      automargin: true,
      autorange: false,
    },
  };

  constructor(
    private dg: MatDialog,
    private el: ElementRef,
  ) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['results']) {
      this.reset();
      this.plot();
    }
  }

  reset() {
    this.data = [];
    this.terms = [];
    this.visibleTerms = [];
  }

  ngOnDestroy(): void {
    PlotlyJS.purge(this.figure.plotEl.nativeElement);
  }

  calculateMonthDifference(date1: string, date2: string) {
    // Convert strings to Date objects
    var firstDate = new Date(date1.concat('-01'));
    var secondDate = new Date(date2.concat('-01'));

    // Calculate the month difference
    var months = (secondDate.getFullYear() - firstDate.getFullYear()) * 12;
    months -= firstDate.getMonth();
    months += secondDate.getMonth();

    // Return the calculated month count
    return months <= 0 ? 0 : months;
  }

  plot() {
    const groupedTermCounts = new Map<string, Map<string, number>>();
    const allTerms: any[] = [];
    const entries = _.get(this.results, 'response.resultSets.0.results');
    const entryCounts = new Map<string, number>();

    entries.forEach((entry: any, index: any) => {
      const date = new Date(_.get(entry, 'collectionDate'));
      const year = date.getFullYear();
      // date parsing does not work without leading 0 in month
      const month = `0${date.getMonth() + 1}`.slice(-2);
      const year_month = `${year}-${month}`;
      const terms = extract_terms([entry]);

      // record the count
      if (!entryCounts.has(year_month)) {
        entryCounts.set(year_month, 0);
      }
      entryCounts.set(year_month, entryCounts.get(year_month)! + 1);

      // Check if year_month is not a key in the map, then create a new Map for this key.
      if (!groupedTermCounts.has(year_month)) {
        groupedTermCounts.set(year_month, new Map<string, number>());
      }

      // Get the Map of term counts for the current year_month.
      const termCounts = groupedTermCounts.get(year_month);

      terms.forEach((term: any) => {
        allTerms.push(term);
        // If term isn't in the map yet, its count is 1.
        if (!termCounts!.has(term.id)) {
          termCounts!.set(term.id, 1);
        } else {
          // If term is already in the map, increment its count.
          termCounts!.set(term.id, termCounts!.get(term.id)! + 1);
        }
      });
    });
    const dates = [...groupedTermCounts.keys()].sort(
      (a: string, b: string) => Date.parse(a) - Date.parse(b),
    );
    const traces: any = [];
    const allFreqs: number[] = [];
    const uniqueTerms = _.uniqBy(allTerms, (term) => term.id);
    this.visibleTerms.push('Total');

    const firstTrace = {
      x: dates,
      y: dates.map((d) => entryCounts.get(d)),
      hovertext: dates.map((d) => `Count - ${entryCounts.get(d)}`),
      hoverlabel: { namelength: -1 },
      mode: 'markers+lines',
      name: 'Total',
      visible: 'default',
      marker: {
        size: 10,
      },
    };

    uniqueTerms.forEach((term: any) => {
      const name: string = term.id;
      const freqs: number[] = [];

      dates.forEach((date: string) => {
        freqs.push(groupedTermCounts.get(date)!.get(name)! ?? 0);
      });
      const trace = {
        x: dates,
        y: freqs,
        hovertext: freqs.map(() => term.label),
        hoverlabel: { namelength: -1 },
        mode: 'markers+lines',
        name: name,
        visible: 'legendonly',
        marker: {
          size: 10,
        },
      };
      allFreqs.push(...freqs);
      traces.push(trace);
    });

    this.data = [firstTrace, ...traces];
    this.terms = [{ id: 'Total', label: 'Total Entries' }, ...uniqueTerms];

    _.set(
      this.layout,
      'width',
      _.max([
        50 * this.calculateMonthDifference(dates[0], dates.at(-1)!) + 50,
        450,
      ]),
    );
    _.set(this.layout, 'height', 600);
    _.set(this.layout, 'yaxis.range', [0, _.max(firstTrace.y)! + 1]);
  }

  async openTermPicker() {
    const { TermPickerDialogComponent } = await import(
      '../term-picker-dialog/term-picker-dialog.component'
    );
    const dialog = this.dg.open(TermPickerDialogComponent, {
      data: {
        terms: this.terms,
        selected: this.visibleTerms,
      },
    });

    dialog.afterClosed().subscribe((selected) => {
      if (_.isEmpty(selected)) return;
      this.visibleTerms = selected;
      this.data = _.map(this.data, (trace: any) => {
        _.set(
          trace,
          'visible',
          this.visibleTerms.includes(trace.name) ? 'default' : 'legendonly',
        );
        return trace;
      });
    });
  }

  async pointClick(e: any) {
    // TODO
  }
}
