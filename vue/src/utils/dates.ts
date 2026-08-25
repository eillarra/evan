import { date as quasardate } from 'quasar';

const formatDate = (date: string, format?: string) => {
  return quasardate.formatDate(date, format || 'YYYY-MM-DD HH:mm');
};

const formatTimeRange = (start?: string | null, end?: string | null): string => {
  if (!start) return '';
  const startTime = quasardate.formatDate(start, 'HH:mm');
  const endTime = end ? quasardate.formatDate(end, 'HH:mm') : '';
  return endTime ? `${startTime}-${endTime}` : startTime;
};

const sumHours = (hourMinutes: string[], asTuple?: boolean) => {
  /* Given a list of strings like HH:mm, return the sum of all hours and minutes.
  If asked for a tuple, return a tuple of hours and minutes, otherwise return a string like HH:mm. */

  let hours = 0;
  let minutes = 0;

  for (const hm of hourMinutes) {
    const [hour, minute] = hm.split(':').map(Number);
    hours += hour;
    minutes += minute;
  }

  hours += Math.floor(minutes / 60);
  minutes = minutes % 60;

  if (asTuple) {
    return [hours, minutes];
  } else {
    const paddedminutes = minutes < 10 ? `0${minutes}` : `${minutes}`;
    return `${hours}:${paddedminutes}`;
  }
};

export { formatDate, formatTimeRange, sumHours };
