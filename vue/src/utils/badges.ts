import {
  iconBadgeAsterisk,
  iconBadgeAudioTour,
  iconBadgeBoatTrip,
  iconBadgeCamera,
  iconBadgeCameraStruck,
  iconBadgeCastle,
  iconBadgeDinner,
  iconBadgeGuidedTour,
  iconBadgeKayaking,
  iconBadgeReception,
  iconBadgeStar,
} from '@/icons';

export type BadgeIcon =
  'reception' | 'dinner' | 'boat_trip' | 'kayaking' | 'guided_tour' | 'audio_tour' | 'castle' | 'star' | 'asterisk';

// Keep in sync with AVAILABLE_BADGE_ICONS in evan/models/documents/badges.py
export const BADGE_ICONS: BadgeIcon[] = [
  'reception',
  'dinner',
  'boat_trip',
  'kayaking',
  'guided_tour',
  'audio_tour',
  'castle',
  'star',
  'asterisk',
];

// Keep in sync with ICON_FILES in evan/models/documents/badges.py
// Values are Material Symbols path data (q-icon names), not file URLs.
const ICON_NAMES: Record<BadgeIcon | 'camera_struck', string> = {
  reception: iconBadgeReception,
  dinner: iconBadgeDinner,
  boat_trip: iconBadgeBoatTrip,
  kayaking: iconBadgeKayaking,
  guided_tour: iconBadgeGuidedTour,
  audio_tour: iconBadgeAudioTour,
  castle: iconBadgeCastle,
  star: iconBadgeStar,
  asterisk: iconBadgeAsterisk,
  camera: iconBadgeCamera,
  camera_struck: iconBadgeCameraStruck,
};

export function badgeIconName(icon: string | null | undefined): string {
  if (!icon) return '';
  return ICON_NAMES[icon as BadgeIcon | 'camera_struck'] ?? '';
}
