import { Injectable } from '@angular/core';
import * as _ from 'lodash';
import { HttpClient } from '@angular/common/http';
import { mergeMap } from 'rxjs';

@Injectable()
export class OntologyService {
  private baseURLOLS = 'https://www.ebi.ac.uk/ols4/api/ontologies';
  private baseURLOntoserver =
    'https://r4.ontoserver.csiro.au/fhir/CodeSystem/$lookup';

  constructor(private http: HttpClient) {}

  private fetchOntologyTermFromOLS(ontology: string, term: string) {
    return this.http
      .get(`${this.baseURLOLS}/${ontology}`)
      .pipe(
        mergeMap((data) =>
          this.http.get(
            `${this.baseURLOLS}/${_.toLower(
              ontology,
            )}/terms/${encodeURIComponent(
              encodeURIComponent(_.get(data, 'config.baseUris.0') + term),
            )}`,
          ),
        ),
      );
  }

  fetch_term_details(term: string) {
    const [ontology, code] = _.split(term, ':');

    return _.toUpper(ontology) === 'SNOMED'
      ? this.http.get(
          `${this.baseURLOntoserver}?system=http://snomed.info/sct&code=${code}`,
        )
      : this.fetchOntologyTermFromOLS(ontology, code);
  }
}
