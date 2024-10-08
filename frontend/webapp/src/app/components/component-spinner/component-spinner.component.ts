import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-component-spinner',
  templateUrl: './component-spinner.component.html',
  styleUrls: ['./component-spinner.component.scss'],
  standalone: true,
})
export class ComponentSpinnerComponent {
  @Input()
  loading: boolean = false;
}
