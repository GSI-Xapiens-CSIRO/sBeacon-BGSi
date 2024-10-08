import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TimeSeriesPlotComponent } from './time-series-plot.component';

describe('TimeSeriesPlotComponent', () => {
  let component: TimeSeriesPlotComponent;
  let fixture: ComponentFixture<TimeSeriesPlotComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TimeSeriesPlotComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(TimeSeriesPlotComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
