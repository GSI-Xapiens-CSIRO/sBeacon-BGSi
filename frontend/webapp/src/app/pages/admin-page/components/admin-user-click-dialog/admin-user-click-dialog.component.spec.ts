import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AdminUserClickDialogComponent } from './admin-user-click-dialog.component';

describe('AdminUserClickDialogComponent', () => {
  let component: AdminUserClickDialogComponent;
  let fixture: ComponentFixture<AdminUserClickDialogComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [AdminUserClickDialogComponent],
    });
    fixture = TestBed.createComponent(AdminUserClickDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
