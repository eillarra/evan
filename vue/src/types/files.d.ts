interface RelatedFile extends ApiObject {
  readonly url: Url;

  type: 'public' | 'private';
  tags: string[];
}
