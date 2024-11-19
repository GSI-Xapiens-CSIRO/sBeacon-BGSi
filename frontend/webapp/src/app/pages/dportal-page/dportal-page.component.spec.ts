import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DportalPageComponent } from './dportal-page.component';

describe('DportalPageComponent', () => {
  let component: DportalPageComponent;
  let fixture: ComponentFixture<DportalPageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DportalPageComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(DportalPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
