import { describe, expect, it } from 'vitest';

import { GENDER_OPTIONS, getAllGenderOptions, getGenderLabel } from '../gender';

describe('GENDER_OPTIONS', () => {
  it('contains the four canonical gender options with matching value/label pairs', () => {
    expect(GENDER_OPTIONS).toEqual([
      { value: 'male', label: 'Male' },
      { value: 'female', label: 'Female' },
      { value: 'non_binary', label: 'Non-binary' },
      { value: 'prefer_not_to_say', label: 'Prefer not to say' },
    ]);
  });
});

describe('getGenderLabel', () => {
  it('returns the human-readable label for a known value', () => {
    expect(getGenderLabel('male')).toBe('Male');
  });

  it('returns Not specified for null', () => {
    expect(getGenderLabel(null)).toBe('Not specified');
  });

  it('returns Not specified for undefined', () => {
    expect(getGenderLabel(undefined)).toBe('Not specified');
  });

  it('returns Not specified for an empty string', () => {
    expect(getGenderLabel('')).toBe('Not specified');
  });

  it('returns the raw value when it is unknown', () => {
    expect(getGenderLabel('helicopter')).toBe('helicopter');
  });
});

describe('getAllGenderOptions', () => {
  it('prepends the none option before the canonical options', () => {
    const all = getAllGenderOptions();
    expect(all[0]).toEqual({ value: 'none', label: 'Not specified' });
    expect(all.slice(1)).toEqual(GENDER_OPTIONS);
  });

  it('has length 5 (none + four canonical)', () => {
    expect(getAllGenderOptions()).toHaveLength(5);
  });
});
