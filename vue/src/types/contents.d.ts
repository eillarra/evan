interface ContentConfig {
  markdown: boolean;
}

interface Content extends ApiObject {
  readonly rel_files: ApiEndpoint;

  key: string;
  value: string | MarkdownText;
  config: ContentConfig;
}
