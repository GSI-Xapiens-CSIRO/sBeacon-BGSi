import { ComponentFixture, TestBed } from '@angular/core/testing';

import { UserProjectFilesComponent } from './user-project-files.component';

describe('UserProjectFilesComponent', () => {
  let component: UserProjectFilesComponent;
  let fixture: ComponentFixture<UserProjectFilesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [UserProjectFilesComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(UserProjectFilesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
