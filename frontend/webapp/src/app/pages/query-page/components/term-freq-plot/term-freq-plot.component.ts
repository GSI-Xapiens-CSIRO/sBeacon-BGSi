import {
  AfterViewInit,
  Component,
  ElementRef,
  Input,
  OnChanges,
  OnDestroy,
  SimpleChanges,
  ViewChild,
} from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { map, find } from 'lodash';
import * as echarts from 'echarts/core';
import {
  TooltipComponent,
  TooltipComponentOption,
  GridComponent,
  GridComponentOption,
} from 'echarts/components';
import { BarChart, BarSeriesOption } from 'echarts/charts';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([TooltipComponent, GridComponent, BarChart, CanvasRenderer]);
type EChartsOption = echarts.ComposeOption<
  TooltipComponentOption | GridComponentOption | BarSeriesOption
>;

@Component({
  selector: 'app-term-freq-plot',
  templateUrl: './term-freq-plot.component.html',
  styleUrls: ['./term-freq-plot.component.scss'],
  standalone: true,
})
export class TermFreqPlotComponent
  implements OnChanges, OnDestroy, AfterViewInit
{
  @Input() counts!: any[];
  @ViewChild('plot') protected figure!: ElementRef;
  protected data: any = null;
  private chart!: echarts.EChartsType;

  constructor(private dg: MatDialog) {}

  ngOnDestroy(): void {
    if (this.chart) {
      echarts.dispose(this.chart);
    }
  }

  ngAfterViewInit(): void {
    if (!this.data) {
      return;
    }
    const dom = this.figure.nativeElement;
    this.chart = this.chart ? this.chart : echarts.init(dom);
    this.chart.on('click', (e) => !!this.barClick(e));
    this.plot();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['counts']) {
      this.data = {
        x: map(this.counts, (word) => word.id),
        y: map(this.counts, (word) => word.count),
        hovertext: map(this.counts, (word) => word.label),
      };
      // if figure loaded
      if (this.figure) {
        this.plot();
      }
    }
  }

  plot() {
    const barWidth = 30; // Constant bar width in pixels
    const minChartWidth = 450; // Minimum chart width in pixels
    const numBars = this.data.x.length; // Number of bars/data points
    const barSpacing = 40; // Estimate space for each bar including margins
    const calculatedChartWidth = Math.max(minChartWidth, numBars * barSpacing);
    const option: EChartsOption = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow',
        },
      },
      grid: {
        left: 10,
        right: 10,
        bottom: 50,
        containLabel: true,
      },
      xAxis: [
        {
          type: 'category',
          data: this.data.x,
          axisTick: {
            alignWithLabel: true,
          },
          axisLabel: {
            rotate: 90,
          },
        },
      ],
      yAxis: [
        {
          type: 'value',
        },
      ],
      series: [
        {
          name: 'Frequency',
          type: 'bar',
          barWidth: barWidth,
          barCategoryGap: 50,
          data: this.data.y,
        },
      ],
    };

    this.chart.setOption(option);
    this.chart.resize({ width: calculatedChartWidth });
  }

  async barClick(e: echarts.ECElementEvent) {
    console.log(e);
    const name = e.name;
    const { WordClickDialogComponent } = await import(
      'src/app/components/word-click-dialog/word-click-dialog.component'
    );
    this.dg.open(WordClickDialogComponent, {
      data: {
        id: name,
        label: find(this.counts, (item: any) => item.id === name).label,
        count: find(this.counts, (item: any) => item.id === name).count,
      },
    });
  }
}
