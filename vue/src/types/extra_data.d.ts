interface ImportantDate {
  label: string;
  format: 'date' | 'range' | 'month';
  start_date: string;
  end_date: string | null;
  aoe: boolean;
}

interface Person {
  id?: string;
  first_name: string;
  last_name: string;
  affiliation: string | null;
  email: string | null;
}

interface Committee {
  name: string;
  members: Person[];
  sorting: 'first_name' | 'last_name';
  display: 'full' | 'list';
}

interface ApiObjectWithDates extends ApiObject {
  extra_data: {
    important_dates: ImportantDate[];
  };
}
