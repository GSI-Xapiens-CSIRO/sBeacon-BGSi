import { Component } from '@angular/core';
import _ from 'lodash';
import { QueryTabComponent } from './components/query-tab/query-tab.component';
import {
  TabBarComponent,
  TabEvent,
  tabAnimations,
} from 'src/app/components/tab-bar/tab-bar.component';

@Component({
  selector: 'app-query-page',
  templateUrl: './query-page.component.html',
  styleUrls: ['./query-page.component.scss'],
  animations: [tabAnimations],
  standalone: true,
  imports: [QueryTabComponent, TabBarComponent],
})
export class QueryPageComponent {
  protected pages = [1];
  protected counter = 1;
  protected active = 1;

  constructor() {}

  changed({ pages, active }: TabEvent) {
    this.active = active;
    this.pages = pages;
  }
}
