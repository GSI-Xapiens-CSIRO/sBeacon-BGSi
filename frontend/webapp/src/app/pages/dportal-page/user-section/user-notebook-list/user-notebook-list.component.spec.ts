import { ComponentFixture, TestBed } from '@angular/core/testing';

import { UserNotebookListComponent } from './user-notebook-list.component';

describe('UserNotebookListComponent', () => {
  let component: UserNotebookListComponent;
  let fixture: ComponentFixture<UserNotebookListComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [UserNotebookListComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(UserNotebookListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
