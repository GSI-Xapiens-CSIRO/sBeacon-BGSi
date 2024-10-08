import { ComponentFixture, TestBed } from '@angular/core/testing';

import { QueryPageComponent } from './query-page.component';

describe('QueryPageComponent', () => {
  let component: QueryPageComponent;
  let fixture: ComponentFixture<QueryPageComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [QueryPageComponent],
    });
    fixture = TestBed.createComponent(QueryPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
