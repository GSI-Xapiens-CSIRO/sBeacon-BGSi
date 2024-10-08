import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VariantIdSelectionDialogComponent } from './variant-id-selection-dialog.component';

describe('VariantIdSelectionDialogComponent', () => {
  let component: VariantIdSelectionDialogComponent;
  let fixture: ComponentFixture<VariantIdSelectionDialogComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [VariantIdSelectionDialogComponent],
    });
    fixture = TestBed.createComponent(VariantIdSelectionDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
