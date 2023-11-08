interface ImportantDate {
  label: string;
  format: 'date' | 'range' | 'month';
  start_date: string;
  end_date: string | null;
  aoe: boolean;
}

interface Person {
  name: string;
  affiliation: string | null;
  country_code: string | null;
  email: string | null;
}

interface ApiObjectWithDates extends ApiObject {
  extra_data: {
    important_dates: ImportantDate[];
  };
}
