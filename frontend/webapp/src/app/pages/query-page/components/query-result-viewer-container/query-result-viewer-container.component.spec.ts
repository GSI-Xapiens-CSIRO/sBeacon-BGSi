import { ComponentFixture, TestBed } from '@angular/core/testing';

import { QueryResultViewerContainerComponent } from './query-result-viewer-container.component';

describe('QueryResultViewerContainerComponent', () => {
  let component: QueryResultViewerContainerComponent;
  let fixture: ComponentFixture<QueryResultViewerContainerComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [QueryResultViewerContainerComponent],
    });
    fixture = TestBed.createComponent(QueryResultViewerContainerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
