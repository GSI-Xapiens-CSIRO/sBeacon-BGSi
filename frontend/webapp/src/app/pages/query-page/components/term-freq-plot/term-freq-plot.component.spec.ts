import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TermFreqPlotComponent } from './term-freq-plot.component';

describe('TermFreqPlotComponent', () => {
  let component: TermFreqPlotComponent;
  let fixture: ComponentFixture<TermFreqPlotComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [TermFreqPlotComponent],
    });
    fixture = TestBed.createComponent(TermFreqPlotComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
