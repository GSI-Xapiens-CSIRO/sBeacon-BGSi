import { ComponentFixture, TestBed } from '@angular/core/testing';

import { QueryTabComponent } from './query-tab.component';

describe('QueryTabComponent', () => {
  let component: QueryTabComponent;
  let fixture: ComponentFixture<QueryTabComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [QueryTabComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(QueryTabComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
