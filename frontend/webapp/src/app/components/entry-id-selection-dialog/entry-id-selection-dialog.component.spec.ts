import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EntryIdSelectionDialogComponent } from './entry-id-selection-dialog.component';

describe('EntryIdSelectionDialogComponent', () => {
  let component: EntryIdSelectionDialogComponent;
  let fixture: ComponentFixture<EntryIdSelectionDialogComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [EntryIdSelectionDialogComponent],
    });
    fixture = TestBed.createComponent(EntryIdSelectionDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
