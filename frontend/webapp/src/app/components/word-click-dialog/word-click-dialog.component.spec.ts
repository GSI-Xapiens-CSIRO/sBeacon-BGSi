import { ComponentFixture, TestBed } from '@angular/core/testing';

import { WordClickDialogComponent } from './word-click-dialog.component';

describe('WordClickDialogComponent', () => {
  let component: WordClickDialogComponent;
  let fixture: ComponentFixture<WordClickDialogComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [WordClickDialogComponent],
    });
    fixture = TestBed.createComponent(WordClickDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
