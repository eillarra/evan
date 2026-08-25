import { describe, expect, it } from 'vitest';

import { formatDate, formatTimeRange, sumHours } from '../dates';

describe('formatDate', () => {
  it('uses the default YYYY-MM-DD HH:mm format when none is given', () => {
    const result = formatDate('2026-08-15T10:45:00');
    expect(result).toBe('2026-08-15 10:45');
  });

  it('honours a custom format string', () => {
    const result = formatDate('2026-08-15T10:45:00', 'DD/MM/YYYY');
    expect(result).toBe('15/08/2026');
  });

  it('formats a date with Quasar month-abbr token as MMM, not date-fns LLL', () => {
    const result = formatDate('2026-08-15T18:01:00', 'MMM D, YYYY HH:mm');
    expect(result).toBe('Aug 15, 2026 18:01');
  });
});

describe('formatTimeRange', () => {
  it('formats a start and end time as HH:mm-HH:mm', () => {
    expect(formatTimeRange('2026-09-03T10:00:00', '2026-09-03T11:30:00')).toBe('10:00-11:30');
  });

  it('returns only the start time when no end is given', () => {
    expect(formatTimeRange('2026-09-03T10:00:00')).toBe('10:00');
  });

  it('returns an empty string when no start is given', () => {
    expect(formatTimeRange('', '2026-09-03T11:30:00')).toBe('');
  });

  it('returns an empty string when both start and end are missing', () => {
    expect(formatTimeRange()).toBe('');
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
