import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FilterSelectionDialogComponent } from './filter-selection-dialog.component';

describe('FilterSelectionDialogComponent', () => {
  let component: FilterSelectionDialogComponent;
  let fixture: ComponentFixture<FilterSelectionDialogComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [FilterSelectionDialogComponent],
    });
    fixture = TestBed.createComponent(FilterSelectionDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
