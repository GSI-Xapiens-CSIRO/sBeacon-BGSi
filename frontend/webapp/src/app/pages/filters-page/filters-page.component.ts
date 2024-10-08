import { Component } from '@angular/core';
import {
  TabBarComponent,
  TabEvent,
  tabAnimations,
} from 'src/app/components/tab-bar/tab-bar.component';
import { FiltersTabComponent } from './components/filters-tab/filters-tab.component';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-filters-page',
  templateUrl: './filters-page.component.html',
  styleUrls: ['./filters-page.component.scss'],
  standalone: true,
  imports: [CommonModule, TabBarComponent, FiltersTabComponent],
  animations: [tabAnimations],
})
export class FiltersPageComponent {
  protected pages = [1];
  protected counter = 1;
  protected active = 1;

  constructor() {}

  changed({ pages, active }: TabEvent) {
    this.active = active;
    this.pages = pages;
  }
}
