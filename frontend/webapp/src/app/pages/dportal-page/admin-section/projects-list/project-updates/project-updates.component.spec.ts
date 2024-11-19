import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ProjectUpdatesComponent } from './project-updates.component';

describe('ProjectUpdatesComponent', () => {
  let component: ProjectUpdatesComponent;
  let fixture: ComponentFixture<ProjectUpdatesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProjectUpdatesComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(ProjectUpdatesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
