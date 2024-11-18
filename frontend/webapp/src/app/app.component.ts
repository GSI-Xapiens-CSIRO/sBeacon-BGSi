import { Component, ElementRef, HostListener, OnInit } from '@angular/core';
import { AuthService } from './services/auth.service';
import {
  animate,
  state,
  style,
  transition,
  trigger,
} from '@angular/animations';
import { AsyncPipe } from '@angular/common';
import {
  RouterLinkActive,
  RouterLink,
  RouterOutlet,
  Router,
  NavigationStart,
  NavigationEnd,
  Event,
  NavigationError,
  NavigationCancel,
} from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { GlobalSpinnerComponent } from './components/global-spinner/global-spinner.component';
import { SpinnerService } from './services/spinner.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
  animations: [
    trigger('collapse', [
      state(
        'open',
        style({
          height: '*',
          opacity: 1,
          visibility: 'visible',
        }),
      ),
      state(
        'closed',
        style({
          height: '0',
          opacity: 0,
          visibility: 'hidden',
        }),
      ),
      transition('open => closed', [animate('0.1s ease-out')]),
      transition('closed => open', [animate('0.1s ease-in')]),
    ]),
  ],
  standalone: true,
  imports: [
    MatButtonModule,
    MatIconModule,
    RouterLinkActive,
    RouterLink,
    RouterOutlet,
    AsyncPipe,
    GlobalSpinnerComponent,
  ],
  providers: [SpinnerService],
})
export class AppComponent implements OnInit {
  protected isCollapsed = false;

  constructor(
    protected auth: AuthService,
    private router: Router,
    private el: ElementRef,
    private ss: SpinnerService,
  ) {
    this.router.events.subscribe((event: Event) => {
      switch (true) {
        case event instanceof NavigationStart: {
          this.ss.start();
          break;
        }
        case event instanceof NavigationEnd:
        case event instanceof NavigationError:
        case event instanceof NavigationCancel: {
          this.ss.end();
          break;
        }
      }
    });
  }

  ngOnInit(): void {
    this.isCollapsed = this.el.nativeElement.offsetWidth < 1200;
    if (!this.auth.user.value) {
      console.log('keinin');
      this.router.navigate(['/login']);
    }
  }

  @HostListener('window:resize', ['event'])
  onResize() {
    this.isCollapsed = this.el.nativeElement.offsetWidth < 1200;
  }
}
