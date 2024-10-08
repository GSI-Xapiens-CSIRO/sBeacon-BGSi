import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TermFreqViewerComponent } from './term-freq-viewer.component';

describe('TermFreqViewerComponent', () => {
  let component: TermFreqViewerComponent;
  let fixture: ComponentFixture<TermFreqViewerComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [TermFreqViewerComponent],
    });
    fixture = TestBed.createComponent(TermFreqViewerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
