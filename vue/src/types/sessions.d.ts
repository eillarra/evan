interface SessionExtraData {
  committees: Committee[];
  important_dates: ImportantDate[];
}

interface SubsessionData {
  title: string;
  order: number;
  program?: string;
  start_at?: string | null | undefined;
  end_at?: string | null | undefined;
}

interface Subsession extends ApiObject, SubsessionData {
  session: number;
  updated_at: string;
}

interface SessionData {
  code: string | null;
  title: string;
  description: MarkdownText;
  program?: string;
  start_at?: string | null | undefined;
  end_at?: string | null | undefined;
  track?: number | null;
  topics?: number[];
  room?: number | null;
  is_social_event: boolean;
  extra_attendees_fee: number;
  extra_data?: SessionExtraData;
}

interface Session extends ApiObject, SessionData {
  secret_url?: Url;
  slug: string;
  updated_at: string;
  extra_data: SessionExtraData;
  subsessions?: Subsession[];
  remaining_capacity: number | null;
  is_full: boolean;
}
