import * as _ from 'lodash';
import { curie } from './parsers';

export const extract_terms = (array: Array<any>): Array<string> => {
  const terms: any = [];
  _.each(array, (item) => {
    if (_.isPlainObject(item)) {
      const label = _.get(item, 'label', '');
      _.forEach(item, (value, key) => {
        if (_.isString(value)) {
          if (key === 'id' && !_.isEmpty(curie.exec(value))) {
            terms.push({
              id: value,
              label: label,
            });
          }
        } else if (_.isPlainObject(value)) {
          terms.push(...extract_terms([value]));
        } else if (_.isArray(value)) {
          terms.push(...extract_terms(value));
        }
      });
    } else if (_.isString(item)) {
      // do nothing;
    } else if (_.isArray(item)) {
      terms.push(...extract_terms(item));
    }
  });
  return terms;
};
