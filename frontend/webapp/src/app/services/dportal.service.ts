import { Injectable } from '@angular/core';
import { API } from 'aws-amplify';
import { from } from 'rxjs';
import { environment } from 'src/environments/environment';

@Injectable({
  providedIn: 'root',
})
export class DportalService {
  constructor() {}

  submitData(s3path: string) {
    console.log('submit dataset', s3path);
    return from(
      API.post(environment.api_endpoint_sbeacon.name, 'submit_dataset', {
        body: { s3Payload: s3path },
      }),
    );
  }

  indexData() {
    console.log('index datasets');
    return from(
      API.post(environment.api_endpoint_sbeacon.name, 'index', {
        body: { reIndexTables: true, reIndexOntologyTerms: true },
      }),
    );
  }

  // data portal user actions
}
