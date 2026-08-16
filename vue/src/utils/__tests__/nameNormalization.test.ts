import { describe, expect, it } from 'vitest';

import { normalizeNameIfAllCaps, toTitleCase } from '../nameNormalization';

describe('toTitleCase', () => {
  it('capitalises the first letter of each word', () => {
    expect(toTitleCase('jean luc picard')).toBe('Jean Luc Picard');
  });

  it('preserves hyphen separators and capitalises each side', () => {
    expect(toTitleCase('jean-luc picard')).toBe('Jean-Luc Picard');
  });

  it('preserves apostrophe separators and capitalises each side', () => {
    expect(toTitleCase("o'brien")).toBe("O'Brien");
  });

  it('lowercases non-first letters within a word', () => {
    expect(toTitleCase('HELLO WORLD')).toBe('Hello World');
  });

  it('handles a single word', () => {
    expect(toTitleCase('picard')).toBe('Picard');
  });
});

describe('normalizeNameIfAllCaps', () => {
  it('converts an all-caps name to title case', () => {
    expect(normalizeNameIfAllCaps('JANE DOE')).toBe('Jane Doe');
  });

  it('leaves a normally-cased name untouched', () => {
    expect(normalizeNameIfAllCaps('Jane Doe')).toBe('Jane Doe');
  });

  it('converts all-caps name with hyphen to title case', () => {
    expect(normalizeNameIfAllCaps('JEAN-LUC PICARD')).toBe('Jean-Luc Picard');
  });

  it('returns an empty string unchanged', () => {
    expect(normalizeNameIfAllCaps('')).toBe('');
  });

  it('trims surrounding whitespace before deciding', () => {
    expect(normalizeNameIfAllCaps('  JANE DOE  ')).toBe('Jane Doe');
  });

  it('leaves a string with no letters unchanged', () => {
    expect(normalizeNameIfAllCaps('123')).toBe('123');
  });

  it('leaves a string with only digits and punctuation unchanged', () => {
    expect(normalizeNameIfAllCaps('!@#')).toBe('!@#');
  });

  it('preserves a mixed-case name that happens to match upper', () => {
    // 'van der Berg' is not all-caps, so it stays as-is.
    expect(normalizeNameIfAllCaps('van der Berg')).toBe('van der Berg');
  });
});
