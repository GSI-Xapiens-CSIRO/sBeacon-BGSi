import { Component, OnDestroy, OnInit } from '@angular/core';
import { Subscription } from 'rxjs';
import { SpinnerService } from 'src/app/services/spinner.service';

@Component({
  selector: 'app-global-spinner',
  templateUrl: './global-spinner.component.html',
  styleUrls: ['./global-spinner.component.scss'],
  standalone: true,
  imports: [],
})
export class GlobalSpinnerComponent implements OnInit, OnDestroy {
  protected loading = false;
  private loadingSub: Subscription | null = null;

  constructor(protected ss: SpinnerService) {
    ss.loading;
  }

  ngOnInit() {
    this.loadingSub = this.ss.loading.subscribe(
      (loading) => (this.loading = loading),
    );
  }

  ngOnDestroy() {
    if (this.loadingSub) {
      this.loadingSub.unsubscribe();
    }
  }
}
