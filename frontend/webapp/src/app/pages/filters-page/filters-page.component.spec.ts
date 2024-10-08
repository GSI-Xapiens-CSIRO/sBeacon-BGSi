import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FiltersPageComponent } from './filters-page.component';

describe('FiltersPageComponent', () => {
  let component: FiltersPageComponent;
  let fixture: ComponentFixture<FiltersPageComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [FiltersPageComponent],
    });
    fixture = TestBed.createComponent(FiltersPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
