import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import {
  animate,
  state,
  style,
  transition,
  trigger,
  sequence,
} from '@angular/animations';
import _ from 'lodash';

export interface TabEvent {
  pages: number[];
  active: number;
}

export const tabAnimations = trigger('navigate', [
  state(
    'open',
    style({
      height: 'auto',
      opacity: 1,
      visibility: 'visible',
    }),
  ),
  state(
    'closed',
    style({
      height: 0,
      opacity: 0,
      visibility: 'hidden',
    }),
  ),
  transition('* => open', [
    sequence([
      style({ height: 'auto', opacity: 0, visibility: 'visible' }),
      animate('0.2s ease-in'),
    ]),
  ]),
]);

@Component({
  selector: 'app-tab-bar',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatChipsModule, MatIconModule],
  templateUrl: './tab-bar.component.html',
  styleUrl: './tab-bar.component.scss',
})
export class TabBarComponent {
  @Output() changed = new EventEmitter<TabEvent>();
  protected pages = [1];
  protected counter = 1;
  protected active = 1;

  close(page: number) {
    const index = _.findIndex(this.pages, (p) => p === page);
    this.pages = _.filter(this.pages, (p) => p !== page);

    if (_.isEmpty(this.pages)) {
      this.pages = [1];
      this.active = this.pages[0];
      this.counter = 1;
    } else {
      this.active = this.pages[_.min([index, this.pages.length - 1])!];
    }
    this.changed.emit({ pages: this.pages, active: this.active });
  }

  append() {
    this.pages.push(++this.counter);
    this.active = this.counter;
    this.changed.emit({ pages: this.pages, active: this.active });
  }
}
