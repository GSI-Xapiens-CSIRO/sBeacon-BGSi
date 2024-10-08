import { Injectable } from '@angular/core';
import { API } from 'aws-amplify';
import { from } from 'rxjs';
import { environment } from 'src/environments/environment';

@Injectable()
export class QueryService {
  constructor() {}

  fetch(scope: string, query: any) {
    console.log('scope', scope, query);
    return from(
      API.post(environment.api_endpoint_sbeacon.name, scope, {
        body: query,
      }),
    );
  }

  fetch_custom(endpoint: string, query: any) {
    console.log('custom scope', endpoint, query);
    return from(
      API.post(environment.api_endpoint_sbeacon.name, endpoint, {
        body: query,
      }),
    );
  }
}
