import { ComponentFixture, TestBed } from '@angular/core/testing';

import { WordCloudPlotComponent } from './word-cloud-plot.component';

describe('WordCloudPlotComponent', () => {
  let component: WordCloudPlotComponent;
  let fixture: ComponentFixture<WordCloudPlotComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [WordCloudPlotComponent],
    });
    fixture = TestBed.createComponent(WordCloudPlotComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
