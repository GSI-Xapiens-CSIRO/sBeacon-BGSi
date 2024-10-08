import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TextQueryResultsViewerComponent } from './text-query-results-viewer.component';

describe('TextQueryResultsViewerComponent', () => {
  let component: TextQueryResultsViewerComponent;
  let fixture: ComponentFixture<TextQueryResultsViewerComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TextQueryResultsViewerComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(TextQueryResultsViewerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
