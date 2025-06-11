export type GenderOption = 'none' | 'male' | 'female' | 'non_binary' | 'prefer_not_to_say';

export interface GenderSelectOption {
  value: GenderOption;
  label: string;
}

export const GENDER_OPTIONS: GenderSelectOption[] = [
  {
    value: 'male',
    label: 'Male',
  },
  {
    value: 'female',
    label: 'Female',
  },
  {
    value: 'non_binary',
    label: 'Non-binary',
  },
  {
    value: 'prefer_not_to_say',
    label: 'Prefer not to say',
  },
] as const;

// Helper function to get the display label for a gender value
export function getGenderLabel(gender: string | undefined | null): string {
  if (!gender) return 'Not specified';

  const option = GENDER_OPTIONS.find((opt) => opt.value === gender);
  return option?.label || gender;
}

// Helper function to get all gender options including 'none'
export function getAllGenderOptions(): GenderSelectOption[] {
  return [{ value: 'none', label: 'Not specified' }, ...GENDER_OPTIONS];
}
