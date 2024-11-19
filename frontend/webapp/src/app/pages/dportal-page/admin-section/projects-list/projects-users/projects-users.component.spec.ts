import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ProjectsUsersComponent } from './projects-users.component';

describe('ProjectsUsersComponent', () => {
  let component: ProjectsUsersComponent;
  let fixture: ComponentFixture<ProjectsUsersComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProjectsUsersComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ProjectsUsersComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
