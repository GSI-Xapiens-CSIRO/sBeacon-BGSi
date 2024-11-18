import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LoginRedirectPageComponent } from './login-redirect-page.component';

describe('LoginRedirectPageComponent', () => {
  let component: LoginRedirectPageComponent;
  let fixture: ComponentFixture<LoginRedirectPageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LoginRedirectPageComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(LoginRedirectPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
