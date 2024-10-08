import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TermPickerDialogComponent } from './term-picker-dialog.component';

describe('TermPickerDialogComponent', () => {
  let component: TermPickerDialogComponent;
  let fixture: ComponentFixture<TermPickerDialogComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TermPickerDialogComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(TermPickerDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
