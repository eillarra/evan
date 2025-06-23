interface BadgesConfig {
  default: string;
  guest: string;
  fee_colors: Record<string, string>;
  sort_by: 'first_name' | 'last_name';
  group_by: 'none' | 'fee' | 'color';
}

interface FeeConfig {
  included_social_events: number[];
}

interface Fee {
  type: string;
  early_value: number | null;
  value: number;
  notes: string;
  config: FeeConfig;
}

interface Topic extends ApiObject {
  name: string;
  position: number;
}

interface Track extends ApiObject {
  name: string;
  position: number;
}

interface EvanEventExtraData {
  badges: BadgesConfig;
  important_dates: ImportantDate[];
}

interface EvanEvent extends ApiObject {
  readonly rel_files: ApiEndpoint;
  readonly code: string;

  name: string;
  full_name: string;
  city: string;
  country: CountryDict;
  presentation: MarkdownText;
  email: string;
  website: Url;
  hashtag: string;
  start_date: string;
  end_date: string;

  registration_start_date: string;
  registration_early_deadline: string | null;
  registration_deadline: string;
  readonly registration_url: Url;
  readonly registrations_count: number;
  readonly accept_by_default: boolean;

  is_virtual: boolean;
  readonly is_active: boolean;
  readonly is_closed: boolean;
  readonly is_open_for_registration: boolean;
  readonly is_open_for_abstract_submission: boolean;

  signature: string;

  readonly fees: Fee[];
  sessions: Session[];
  topics: Topic[];
  tracks: Track[];

  registration_configuration: EvanEventRegistrationConfig;
  extra_data: EvanEventExtraData;
}

interface ManagedEvanEvent extends EvanEvent {}
