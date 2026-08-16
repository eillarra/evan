import { describe, expect, it } from 'vitest';

import { formatCurrency, formatDecimal } from '../numbers';

describe('formatCurrency', () => {
  it('prefixes the euro symbol by default', () => {
    expect(formatCurrency(50)).toBe('€ 50');
  });

  it('uses the provided symbol when given', () => {
    expect(formatCurrency(50, '$')).toBe('$ 50');
  });

  it('localises the amount via nl-BE grouping', () => {
    expect(formatCurrency(1500)).toBe('€ 1.500');
  });
});

describe('formatDecimal', () => {
  it('formats a decimal with nl-BE one-digit precision', () => {
    expect(formatDecimal(1.5)).toBe('1,5');
  });

  it('rounds to a single fractional digit', () => {
    expect(formatDecimal(2.56)).toBe('2,6');
  });
});
