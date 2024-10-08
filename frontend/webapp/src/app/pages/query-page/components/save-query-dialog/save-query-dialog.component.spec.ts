import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SaveQueryDialogComponent } from './save-query-dialog.component';

describe('SaveQueryDialogComponent', () => {
  let component: SaveQueryDialogComponent;
  let fixture: ComponentFixture<SaveQueryDialogComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [SaveQueryDialogComponent],
    });
    fixture = TestBed.createComponent(SaveQueryDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
