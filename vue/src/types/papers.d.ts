interface PaperAuthor {
  name: string;
  affiliation: string;
}

interface PaperExtraData {
  authors_str: string;
  authors: PaperAuthor[];
}

interface PaperData {
  title: string;
  abstract: MarkdownText;
  track?: number | null;
  topics?: number[];
  extra_data?: PaperExtraData;
}

interface Paper extends ApiObject, PaperData {
  secret_url?: Url;
  updated_at: string;
  extra_data: PaperExtraData;
}
