import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ProjectAssignmentsComponent } from './project-assignments.component';

describe('ProjectAssignmentsComponent', () => {
  let component: ProjectAssignmentsComponent;
  let fixture: ComponentFixture<ProjectAssignmentsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProjectAssignmentsComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(ProjectAssignmentsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
