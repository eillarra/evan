export interface SessionSelectionState {
  registrantSessionIds: number[];
  accompanyingPersonSessionIds: number[][];
}

export function countSessionSelections(sessionId: number, state: SessionSelectionState): number {
  const inRegistrant = state.registrantSessionIds.includes(sessionId) ? 1 : 0;
  const inAccompanyingPersons = state.accompanyingPersonSessionIds.filter((ids) => ids.includes(sessionId)).length;

  return inRegistrant + inAccompanyingPersons;
}

/**
 * A session selection is disabled once its capacity is exhausted, unless the bearer
 * (the registrant or an accompanying person) already holds that slot - so it stays
 * uncheckable, not unremovable.
 *
 * Capacity is checked against the number of *new* reservations made in this form
 * session (current minus original selections), since `remainingCapacity` already
 * accounts for whatever was persisted when the form was loaded.
 */
export function isSessionSelectionDisabled(
  sessionId: number,
  remainingCapacity: number | null,
  isSelectedByBearer: boolean,
  currentState: SessionSelectionState,
  originalState: SessionSelectionState,
): boolean {
  if (isSelectedByBearer || remainingCapacity === null) {
    return false;
  }

  const netNewReservations =
    countSessionSelections(sessionId, currentState) - countSessionSelections(sessionId, originalState);

  return netNewReservations >= remainingCapacity;
}
