import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TabularQueryResultsViewerComponent } from './tabular-query-results-viewer.component';

describe('TabularQueryResultsViewerComponent', () => {
  let component: TabularQueryResultsViewerComponent;
  let fixture: ComponentFixture<TabularQueryResultsViewerComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TabularQueryResultsViewerComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(TabularQueryResultsViewerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
