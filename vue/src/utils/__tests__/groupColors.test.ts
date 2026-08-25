import { describe, expect, it } from 'vitest';

import { stringToColor } from '../groupColors';

describe('stringToColor', () => {
  it('returns a hex color for a non-empty string', () => {
    expect(stringToColor('Parallel slot 1')).toMatch(/^#[0-9A-Fa-f]{6}$/);
  });

  it('is deterministic — same input always yields the same color', () => {
    expect(stringToColor('Parallel slot 1')).toBe(stringToColor('Parallel slot 1'));
  });

  it('distributes different groups across the palette', () => {
    const colors = new Set(['Parallel slot 1', 'Parallel slot 2', 'Parallel slot 3'].map(stringToColor));
    expect(colors.size).toBe(3);
  });

  it('uses a wide-enough palette that common groups stay distinct', () => {
    const groups = ['Parallel slot 1', 'Parallel slot 2', 'Parallel slot 3', 'Parallel slot 4', 'Parallel slot 5'];
    const colors = new Set(groups.map(stringToColor));
    expect(colors.size).toBeGreaterThanOrEqual(4);
  });
});
