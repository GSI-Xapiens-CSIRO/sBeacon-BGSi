import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DataSubmissionFormComponent } from './data-submission-form.component';

describe('DataSubmissionFormComponent', () => {
  let component: DataSubmissionFormComponent;
  let fixture: ComponentFixture<DataSubmissionFormComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DataSubmissionFormComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(DataSubmissionFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
