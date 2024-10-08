import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AdvancedQueryResultsViewerComponent } from './advanced-query-results-viewer.component';

describe('AdvancedQueryResultsViewerComponent', () => {
  let component: AdvancedQueryResultsViewerComponent;
  let fixture: ComponentFixture<AdvancedQueryResultsViewerComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AdvancedQueryResultsViewerComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(AdvancedQueryResultsViewerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
