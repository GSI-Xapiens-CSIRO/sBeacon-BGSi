import {
  AfterViewInit,
  Component,
  ElementRef,
  Input,
  OnChanges,
  ViewChild,
} from '@angular/core';
import * as _ from 'lodash';
import { colors as colorWheel } from 'src/app/utils/utils';
import { MatDialog } from '@angular/material/dialog';
import WordCloud from 'wordcloud';
import { ComponentSpinnerComponent } from '../../../../components/component-spinner/component-spinner.component';

interface CloudWord {
  size: number;
  text: string;
  label: string;
  color: string;
  count: number;
}

@Component({
  selector: 'app-word-cloud-plot',
  templateUrl: './word-cloud-plot.component.html',
  styleUrls: ['./word-cloud-plot.component.scss'],
  standalone: true,
  imports: [ComponentSpinnerComponent],
})
export class WordCloudPlotComponent implements OnChanges, AfterViewInit {
  @Input() counts!: any[];
  @ViewChild('figure') protected figure!: ElementRef;
  protected loading = true;

  constructor(private dg: MatDialog) {}

  ngAfterViewInit(): void {
    this.loading = true;
    this.plot();
    this.figure.nativeElement.addEventListener('wordcloudstop', () => {
      setTimeout(() => {
        this.loading = false;
      }, 1000);
    });
  }

  ngOnChanges(): void {
    this.loading = true;
    if (this.figure) this.plot();
  }

  plot() {
    const highest = this.counts[0].count;
    const colors: { [key: string]: string } = {};
    let pos = 0;
    _.each(this.counts, (entry: any) => {
      _.set(colors, entry.id, colorWheel[pos]);
      pos++;

      if (pos === colorWheel.length) {
        pos = 0;
      }
    });
    const wordObjects: CloudWord[] = _.map(this.counts, (entry: any) => ({
      text: entry.id,
      label: entry.label,
      count: entry.count,
      size: Math.round(2 + (10 * entry.count) / highest),
      color: colors[entry.id],
    }));

    WordCloud(this.figure.nativeElement, {
      shrinkToFit: true,
      drawOutOfBound: false,
      gridSize: Math.round((16 * this.figure.nativeElement.width) / 1024),
      rotateRatio: 0.5,
      rotationSteps: 2,
      weightFactor: (size: number) => {
        return (Math.pow(size, 2.3) * this.figure.nativeElement.width) / 1024;
      },
      list: _.reverse(
        _.sortBy(
          _.map(wordObjects, (word) => [word.text, word.size]) as any,
          (item) => item[1],
        ),
      ),
      click: async (e: any) => {
        const { WordClickDialogComponent } = await import(
          'src/app/components/word-click-dialog/word-click-dialog.component'
        );
        this.dg.open(WordClickDialogComponent, {
          data: {
            id: e[0],
            label: _.find(this.counts, (item: any) => item.id === e[0]).label,
            count: _.find(this.counts, (item: any) => item.id === e[0]).count,
          },
        });
      },
    });
  }
}
