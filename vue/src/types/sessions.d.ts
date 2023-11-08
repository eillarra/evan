interface TopicCreateData {
  name: string;
}

interface Topic extends ApiObject, TopicCreateData {
  slug?: string;
}

interface TrackCreateData {
  name: string;
  position?: number;
}

interface Track extends ApiObject, TrackCreateData {
  slug?: string;
}

interface SessionExtraData {
  chairs: Person[];
  program_committee: Person[];
  important_dates: ImportantDate[];
}

interface SessionCreateData {
  code: string;
  title: string;
  description: MarkdownText;
  start_at?: string | null | undefined;
  end_at?: string | null | undefined;
  track?: number | null;
  topics?: number[];
  extra_data?: SessionExtraData;
}

interface Session extends ApiObject, SessionCreateData {
  secret_url?: Url;
  slug: string;
  updated_at: string;
  extra_data: SessionExtraData;
}
