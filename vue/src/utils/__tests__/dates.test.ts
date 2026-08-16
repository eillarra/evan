import { describe, expect, it } from 'vitest';

import { formatDate, sumHours } from '../dates';

describe('formatDate', () => {
  it('uses the default YYYY-MM-DD HH:mm format when none is given', () => {
    const result = formatDate('2026-08-15T10:45:00');
    expect(result).toBe('2026-08-15 10:45');
  });

  it('honours a custom format string', () => {
    const result = formatDate('2026-08-15T10:45:00', 'DD/MM/YYYY');
    expect(result).toBe('15/08/2026');
  });
});

describe('sumHours', () => {
  it('sums hour:minute strings into a padded HH:mm string', () => {
    expect(sumHours(['1:30', '2:45'])).toBe('4:15');
  });

  it('returns a [hours, minutes] tuple when asTuple is true', () => {
    expect(sumHours(['1:30', '2:45'], true)).toEqual([4, 15]);
  });

  it('rolls minutes overflow into hours', () => {
    expect(sumHours(['0:50', '0:20'])).toBe('1:10');
  });

  it('pads single-digit minutes with a leading zero', () => {
    expect(sumHours(['1:05'])).toBe('1:05');
  });

  it('returns 0:00 for an empty list as a string', () => {
    expect(sumHours([])).toBe('0:00');
  });

  it('returns [0, 0] for an empty list as a tuple', () => {
    expect(sumHours([], true)).toEqual([0, 0]);
  });
});
