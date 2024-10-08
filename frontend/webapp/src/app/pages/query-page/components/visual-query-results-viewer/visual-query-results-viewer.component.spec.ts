import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VisualQueryResultsViewerComponent } from './visual-query-results-viewer.component';

describe('VisualQueryResultsViewerComponent', () => {
  let component: VisualQueryResultsViewerComponent;
  let fixture: ComponentFixture<VisualQueryResultsViewerComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VisualQueryResultsViewerComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(VisualQueryResultsViewerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
