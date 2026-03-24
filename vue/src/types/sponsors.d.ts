interface SponsorData {
  name: string;
  website: string;
  level: number;
}

interface Sponsor extends ApiObject, SponsorData {
  readonly rel_files: ApiEndpoint;
  readonly files: RelatedFile[];
}
