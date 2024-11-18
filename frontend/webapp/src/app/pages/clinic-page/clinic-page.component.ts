import { Component } from '@angular/core';
import {
  TabBarComponent,
  TabEvent,
  tabAnimations,
} from 'src/app/components/tab-bar/tab-bar.component';
// import { FiltersTabComponent } from './components/filters-tab/filters-tab.component';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-filters-page',
  templateUrl: './clinic-page.component.html',
  styleUrls: ['./clinic-page.component.scss'],
  standalone: true,
  imports: [CommonModule],
  animations: [tabAnimations],
})
export class ClinicPageComponent {
  protected pages = [1];
  protected counter = 1;
  protected active = 1;

  constructor() {}

  changed({ pages, active }: TabEvent) {
    this.active = active;
    this.pages = pages;
  }
}
