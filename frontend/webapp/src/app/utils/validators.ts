import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';
import _ from 'lodash';
import { environment } from 'src/environments/environment';

/**
 * Custom validator function to validate base positions/range format and limit.
 */
export const baseRangeValidator = (): ValidatorFn => {
  const regex = /^[0-9]+(,[0-9]+)?$/;
  return (control: AbstractControl): ValidationErrors | null => {
    const valid = regex.test(control.value);

    if (!valid) {
      return { error: 'Invalid position/range' };
    }

    const range = _.split(control.value, ',');

    if (
      range.length == 2 &&
      parseInt(range[1]) - parseInt(range[0]) >
        environment.config_max_variant_search_base_range
    ) {
      return { error: 'Range exceeds limit' };
    } else if (range.length == 2 && parseInt(range[1]) <= parseInt(range[0])) {
      return { error: 'Invalid range' };
    }
    return null;
  };
};

/**
 * Custom validator function to validate the base range between start and end points.
 */
export const twoRangesValidator = (): ValidatorFn => {
  return (control: AbstractControl): ValidationErrors | null => {
    const start = _.map(_.split(control.get('start')!.value, ','), parseInt);
    const end = _.map(_.split(control.get('end')!.value, ','), parseInt);

    if (start.length === 1 && end.length === 1) {
      if (start[0] >= end[0]) {
        return {
          error: 'Invalid base range, end base must be larger than start base',
        };
      } else if (
        Math.abs(start[0] - end[0]) >
        environment.config_max_variant_search_base_range
      ) {
        return { error: 'Range exceeds the limit' };
      }
    } else if (start.length === 2 && end.length === 1) {
      if (
        Math.abs(end[0] - start[0]) >
        environment.config_max_variant_search_base_range
      ) {
        return { error: 'Range exceeds the limit' };
      }
    } else if (start.length === 1 && end.length === 2) {
      if (
        Math.abs(end[1] - start[0]) >
        environment.config_max_variant_search_base_range
      ) {
        return { error: 'Range exceeds the limit' };
      }
    }
    return null;
  };
};

/**
 * ACGT/acgt/N validation of reference/alternate  alleles
 */
export const acgtNValidator = (): ValidatorFn => {
  const regex = /(^[ACGT]+$)|(^N$)/;
  return (control: AbstractControl): ValidationErrors | null => {
    const valid = regex.test(control.value);
    return valid ? null : { acgt: { value: control.value } };
  };
};
