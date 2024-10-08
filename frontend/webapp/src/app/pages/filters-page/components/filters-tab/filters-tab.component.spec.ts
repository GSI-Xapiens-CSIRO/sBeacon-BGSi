import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FiltersTabComponent } from './filters-tab.component';

describe('FiltersTabComponent', () => {
  let component: FiltersTabComponent;
  let fixture: ComponentFixture<FiltersTabComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FiltersTabComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(FiltersTabComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
