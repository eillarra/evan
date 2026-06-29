export function toTitleCase(value: string): string {
  const normalized = value.toLocaleLowerCase();

  return normalized
    .split(/([\s'-]+)/)
    .map((part) => {
      if (/^[\s'-]+$/.test(part)) {
        return part;
      }

      return part.charAt(0).toLocaleUpperCase() + part.slice(1);
    })
    .join('');
}

export function normalizeNameIfAllCaps(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) {
    return trimmed;
  }

  const hasLetter = /\p{L}/u.test(trimmed);
  const isAllCaps = trimmed === trimmed.toLocaleUpperCase();
  if (!hasLetter || !isAllCaps) {
    return trimmed;
  }

  return toTitleCase(trimmed);
}
