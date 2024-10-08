import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VariantEditorComponent } from './variant-editor.component';

describe('VariantEditorComponent', () => {
  let component: VariantEditorComponent;
  let fixture: ComponentFixture<VariantEditorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VariantEditorComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(VariantEditorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
