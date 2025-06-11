interface KeynoteExtraData {
  speaker_affiliation?: string;
  speaker_website?: string;
  presentation_url?: string;
}

interface KeynoteData {
  code: string;
  title: string;
  speaker: string;
  bio: MarkdownText;
  abstract: MarkdownText;
  session?: number | null;
  subsession?: number | null;
  topics?: number[];
  extra_data?: KeynoteExtraData;
}

interface Keynote extends ApiObject, KeynoteData {
  readonly rel_files: ApiEndpoint;
  secret_url?: Url;
  updated_at: string;
  extra_data: KeynoteExtraData;
}
