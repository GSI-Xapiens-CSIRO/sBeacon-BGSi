import { Injectable } from '@angular/core';
import { API } from 'aws-amplify';
import * as _ from 'lodash';
import { from, map, retry } from 'rxjs';
import { environment } from 'src/environments/environment';

@Injectable()
export class FilterService {
  constructor() {}

  fetch_by_scope(scope: string, query: any) {
    console.log('scope', scope, query);
    return from(
      API.get(
        environment.api_endpoint_sbeacon.name,
        `${scope}/filtering_terms`,
        {
          queryStringParameters: query,
        },
      ),
    );
  }

  fetch_by_scope_and_id(scope: string, id: string, query: any) {
    console.log('scope', scope, query);
    return from(
      API.get(
        environment.api_endpoint_sbeacon.name,
        `${scope}/${id}/filtering_terms`,
        {
          queryStringParameters: query,
        },
      ),
    );
  }

  fetch_counts_by_scope_and_term(scope: string, term: any) {
    const query = {
      query: {
        filters: [term],
        requestedGranularity: 'count',
      },
      meta: {
        apiVersion: 'v2.0',
      },
    };
    return from(
      API.post(environment.api_endpoint_sbeacon.name, scope, {
        body: query,
      }),
    ).pipe(
      map((data: any) => _.get(data, 'responseSummary.numTotalResults', 0)),
      retry({ delay: 2000, count: 3 }),
    );
  }
}
