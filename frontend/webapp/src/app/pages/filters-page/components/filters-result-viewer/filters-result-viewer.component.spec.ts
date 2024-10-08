import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FiltersResultViewerComponent } from './filters-result-viewer.component';

describe('FiltersResultViewerComponent', () => {
  let component: FiltersResultViewerComponent;
  let fixture: ComponentFixture<FiltersResultViewerComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [FiltersResultViewerComponent],
    });
    fixture = TestBed.createComponent(FiltersResultViewerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
