import * as _ from 'lodash';
import { Filter, FilterTypes } from './interfaces';

export const curie = new RegExp('^\\w[^:]+:.+$');

export const parseFilters = (
  filters: Array<any>,
  defaultScope: string,
): Array<Filter> => {
  return _.map(filters, (filter) => {
    const id = _.get(filter, 'id');
    const operator = _.get(filter, 'operator', '');
    const value = _.get(filter, 'value', '');
    const isCurie = !_.isEmpty(curie.exec(id));
    const includeDescendantTerms = _.get(
      filter,
      'includeDescendantTerms',
      true,
    );
    const type = isCurie
      ? FilterTypes.ONTOLOGY
      : _.isEmpty(operator) && _.isEmpty(value)
        ? FilterTypes.CUSTOM
        : FilterTypes.ALPHANUMERIC;

    switch (type) {
      case FilterTypes.ALPHANUMERIC:
        return {
          type: FilterTypes.ALPHANUMERIC,
          scope: defaultScope,
          id,
          operator,
          value,
        };
      case FilterTypes.ONTOLOGY:
        return {
          type: FilterTypes.ONTOLOGY,
          scope: _.get(filter, 'scope', defaultScope),
          id,
          includeDescendantTerms,
        };
      case FilterTypes.CUSTOM:
        return {
          type: FilterTypes.CUSTOM,
          scope: defaultScope,
          id,
        };
      default:
        throw new Error('Critical Error, unable to parse file ' + filter);
    }
  });
};

export const serializeFilters = (
  filters: Array<Filter>,
  defaultScope: string,
): Array<any> => {
  return _.map(filters, (filter) => {
    switch (filter.type) {
      case FilterTypes.ALPHANUMERIC:
        return {
          scope: defaultScope,
          id: filter.id,
          operator: filter.operator,
          value: filter.value,
        };
      case FilterTypes.ONTOLOGY:
        return {
          scope: filter.scope,
          id: filter.id,
          includeDescendantTerms: filter.includeDescendantTerms,
        };
      case FilterTypes.CUSTOM:
        return {
          scope: defaultScope,
          id: filter.id,
        };
      default:
        throw new Error('Critical Error, unable to parse file ' + filter);
    }
  });
};

export const serializeRequestParameters = (params: any): any => {
  const start = params.start;
  const end = params.end;
  const copy = _.cloneDeep(params);

  _.set(copy, 'start', _.split(start, ','));
  _.set(copy, 'end', _.split(end, ','));

  return copy;
};

export const parseRequestParameters = (params: any): any => {
  const start = params.start;
  const end = params.end;
  const copy = _.cloneDeep(params);

  _.set(copy, 'start', _.split(start, ','));
  _.set(copy, 'end', _.split(end, ','));

  return copy;
};
