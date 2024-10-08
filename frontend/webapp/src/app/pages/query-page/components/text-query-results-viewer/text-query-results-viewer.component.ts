import { Component, Input } from '@angular/core';
import { environment } from 'src/environments/environment';
import { NgxJsonViewerModule } from 'ngx-json-viewer';
import { MatExpansionModule } from '@angular/material/expansion';

@Component({
  selector: 'app-text-query-results-viewer',
  templateUrl: './text-query-results-viewer.component.html',
  styleUrl: './text-query-results-viewer.component.scss',
  standalone: true,
  imports: [MatExpansionModule, NgxJsonViewerModule],
})
export class TextQueryResultsViewerComponent {
  @Input({ required: true })
  endpoint: any;
  @Input({ required: true })
  query: any;
  @Input({ required: true })
  results: any;
  protected queryJSONOpen = false;
  protected metaJSONOpen = false;
  protected responseJSONOpen = false;
  protected fullJSONOpen = false;
  protected api = environment.api_endpoint_sbeacon.endpoint;
}
