import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EntityCountsByTermPlotComponent } from './entity-counts-by-term-plot.component';

describe('EntityCountsByTermPlotComponent', () => {
  let component: EntityCountsByTermPlotComponent;
  let fixture: ComponentFixture<EntityCountsByTermPlotComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [EntityCountsByTermPlotComponent],
    });
    fixture = TestBed.createComponent(EntityCountsByTermPlotComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
