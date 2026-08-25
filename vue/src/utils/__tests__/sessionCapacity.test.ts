import { describe, expect, it } from 'vitest';

import { countSessionSelections, isSessionSelectionDisabled, type SessionSelectionState } from '../sessionCapacity';

const emptyState = (): SessionSelectionState => ({ registrantSessionIds: [], accompanyingPersonSessionIds: [] });

describe('countSessionSelections', () => {
  it('counts the registrant and each accompanying person selecting the session', () => {
    const state: SessionSelectionState = {
      registrantSessionIds: [1],
      accompanyingPersonSessionIds: [[1, 2], [1], [2]],
    };

    expect(countSessionSelections(1, state)).toBe(3);
    expect(countSessionSelections(2, state)).toBe(2);
    expect(countSessionSelections(3, state)).toBe(0);
  });
});

describe('isSessionSelectionDisabled', () => {
  it('is never disabled when the session is uncapped', () => {
    expect(isSessionSelectionDisabled(1, null, false, emptyState(), emptyState())).toBe(false);
  });

  it('is never disabled for a bearer who already holds the slot', () => {
    const current: SessionSelectionState = { registrantSessionIds: [1], accompanyingPersonSessionIds: [] };
    expect(isSessionSelectionDisabled(1, 0, true, current, current)).toBe(false);
  });

  it('is disabled once new reservations made in this form reach the remaining capacity', () => {
    const original = emptyState();
    const current: SessionSelectionState = { registrantSessionIds: [], accompanyingPersonSessionIds: [[1]] };

    // One slot remaining, one new reservation already made by an accompanying person.
    expect(isSessionSelectionDisabled(1, 1, false, current, original)).toBe(true);
  });

  it('is not disabled while new reservations stay below the remaining capacity', () => {
    const original = emptyState();
    const current: SessionSelectionState = { registrantSessionIds: [], accompanyingPersonSessionIds: [[1]] };

    expect(isSessionSelectionDisabled(1, 2, false, current, original)).toBe(false);
  });

  it('disables a different bearer when the only slot is already held by someone else', () => {
    const original: SessionSelectionState = { registrantSessionIds: [1], accompanyingPersonSessionIds: [] };
    const current: SessionSelectionState = { registrantSessionIds: [1], accompanyingPersonSessionIds: [] };

    // remaining_capacity (0) already accounts for the registrant's persisted slot.
    expect(isSessionSelectionDisabled(1, 0, false, current, original)).toBe(true);
  });

  it('ignores new reservations made for a different session', () => {
    const original: SessionSelectionState = { registrantSessionIds: [], accompanyingPersonSessionIds: [] };
    const current: SessionSelectionState = { registrantSessionIds: [2], accompanyingPersonSessionIds: [] };

    // Session 2 gained a new reservation, session 1's own count is unaffected.
    expect(isSessionSelectionDisabled(1, 1, false, current, original)).toBe(false);
  });
});
