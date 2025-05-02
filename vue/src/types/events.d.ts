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
  important_dates: ImportantDate[];
}

interface EvanEvent extends ApiObject {
  readonly rel_files: ApiEndpoint;
  readonly code: string;

  name: string;
  full_name: string;
  presentation: MarkdownText;
  email: string;
  website: Url;
  hashtag: string;

  registration_start_date: string;
  registration_early_deadline: string | null;
  registration_deadline: string;
  registration_url: Url;

  is_active: boolean;
  is_closed: boolean;
  is_virtual: boolean;
  is_open_for_registration: boolean;
  is_open_for_abstract_submission: boolean;

  fees: Fee[];
  sessions: Session[];
  topics: Topic[];
  tracks: Track[];

  registration_configuration: EvanEventRegistrationConfig;
  extra_data?: EvanEventExtraData;
}

interface ManagedEvanEvent extends EvanEvent {}
