interface TopicData {
  name: string;
}

interface Topic extends ApiObject, TopicData {
  slug?: string;
}

interface TrackData {
  name: string;
  position?: number;
}

interface Track extends ApiObject, TrackData {
  slug?: string;
}

interface SessionExtraData {
  committees: Committee[];
  important_dates: ImportantDate[];
}

interface SessionData {
  code: string;
  title: string;
  description: MarkdownText;
  start_at?: string | null | undefined;
  end_at?: string | null | undefined;
  track?: number | null;
  topics?: number[];
  is_social_event: boolean;
  extra_attendees_fee: number;
  extra_data?: SessionExtraData;
}

interface Session extends ApiObject, SessionData {
  secret_url?: Url;
  slug: string;
  updated_at: string;
  extra_data: SessionExtraData;
}
