import _ from 'lodash';
import { catchError, of } from 'rxjs';
import { ScopeTypes } from 'src/app/utils/interfaces';

const variant_to_individuals_query = (that: any) => {
  that.reset();
  that.customQuery = true;
  that.ss.start();

  const query = {
    query: {
      filters: [],
      requestedGranularity: 'record',
      requestParameters: {
        assemblyId: 'GRCH38',
        referenceBases: 'N',
        start: [657000],
        end: [659000],
        referenceName: '1',
      },
      pagination: {
        skip: 0,
        limit: 1,
      },
    },
    meta: {
      apiVersion: 'v2.0',
    },
  };

  let result$ = that.qs.fetch(ScopeTypes.GENOMIC_VARIANTS, query);

  result$.pipe(catchError(() => of(null))).subscribe((results: any) => {
    if (results) {
      const variantInternalID =
        results.response.resultSets[0].results[0].variantInternalId;
      const query = {
        query: {
          filters: [],
          requestedGranularity: 'record',
        },
        meta: {
          apiVersion: 'v2.0',
        },
      };
      const result$ = that.qs.fetch_custom(
        `${ScopeTypes.GENOMIC_VARIANTS}/${variantInternalID}/${ScopeTypes.INDIVIDUALS}`,
        query,
      );
      that.scope = ScopeTypes.INDIVIDUALS;
      that.endpoint;

      result$.pipe(catchError(() => of(null))).subscribe((results: any) => {
        if (results) {
          that.results = results;
          that.endpoint = `${ScopeTypes.GENOMIC_VARIANTS}/${variantInternalID}/${ScopeTypes.INDIVIDUALS}`;
          that.scope = ScopeTypes.INDIVIDUALS;
          that.query = query;
          that.sb.open('Query successful!', 'Okay', { duration: 5000 });
        } else {
          that.sb.open(
            'API request failed. Please check your parameters.',
            'Okay',
            { duration: 60000 },
          );
        }

        that.ss.end();
      });
    } else {
      that.sb.open(
        'API request failed. Please check your parameters.',
        'Okay',
        { duration: 60000 },
      );

      that.ss.end();
    }
  });
};

export const customQueries = [
  {
    text: `Records of <strong>individuals</strong> having a variant in <strong>GRCH38: Chr 1</strong> within base range <strong>657000</strong> to <strong>659000</strong>.`,
    func: variant_to_individuals_query,
  },
];
