interface RelatedFile extends ApiObject {
  readonly file: Url;

  visibility: 'public' | 'attendees' | 'organizers';
  description: string;
  tags: string[];
}
