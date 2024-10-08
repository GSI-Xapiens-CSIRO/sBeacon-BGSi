import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ComponentSpinnerComponent } from './component-spinner.component';

describe('ComponentSpinnerComponent', () => {
  let component: ComponentSpinnerComponent;
  let fixture: ComponentFixture<ComponentSpinnerComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [ComponentSpinnerComponent],
    });
    fixture = TestBed.createComponent(ComponentSpinnerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
