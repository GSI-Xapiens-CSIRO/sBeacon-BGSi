import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NotebookItemComponent } from './notebook-item.component';

describe('NotebookItemComponent', () => {
  let component: NotebookItemComponent;
  let fixture: ComponentFixture<NotebookItemComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NotebookItemComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(NotebookItemComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
