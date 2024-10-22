import { ComponentFixture, TestBed } from '@angular/core/testing';

import { UserFileListComponent } from './user-file-list.component';

describe('UserFileListComponent', () => {
  let component: UserFileListComponent;
  let fixture: ComponentFixture<UserFileListComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [UserFileListComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(UserFileListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
