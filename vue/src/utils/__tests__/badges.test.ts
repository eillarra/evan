import { describe, expect, it } from 'vitest';

import { iconBadgeBoatTrip } from '@/icons';

import { BADGE_ICONS, badgeIconName } from '../badges';

describe('BADGE_ICONS', () => {
  it('stays within the ~10 icon whitelist', () => {
    expect(BADGE_ICONS.length).toBeGreaterThanOrEqual(5);
    expect(BADGE_ICONS.length).toBeLessThanOrEqual(10);
  });

  it('contains unique entries', () => {
    expect(new Set(BADGE_ICONS).size).toBe(BADGE_ICONS.length);
  });

  it('resolves every icon key to a q-icon name', () => {
    for (const icon of BADGE_ICONS) {
      expect(badgeIconName(icon), `icon "${icon}" has no frontend mapping`).toBeTruthy();
    }
  });
});

describe('badgeIconName', () => {
  it('maps each icon key to a distinct q-icon name', () => {
    expect(badgeIconName('boat_trip')).toBe(iconBadgeBoatTrip);
    expect(new Set(BADGE_ICONS.map((icon) => badgeIconName(icon))).size).toBe(BADGE_ICONS.length);
  });

  it('resolves the internal camera_struck key', () => {
    expect(badgeIconName('camera_struck')).toBeTruthy();
  });

  it('returns an empty string for missing icons', () => {
    expect(badgeIconName(null)).toBe('');
    expect(badgeIconName(undefined)).toBe('');
    expect(badgeIconName('does_not_exist')).toBe('');
  });
});
