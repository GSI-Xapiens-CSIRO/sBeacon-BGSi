import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GlobalSpinnerComponent } from './global-spinner.component';

describe('SpinnerComponent', () => {
  let component: GlobalSpinnerComponent;
  let fixture: ComponentFixture<GlobalSpinnerComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [GlobalSpinnerComponent],
    });
    fixture = TestBed.createComponent(GlobalSpinnerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
