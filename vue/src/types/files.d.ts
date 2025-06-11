interface RelatedFile extends ApiObject {
  readonly file: Url;

  type: 'public' | 'private';
  description: string;
  tags: string[];
}
