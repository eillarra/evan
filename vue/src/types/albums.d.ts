interface Album extends ApiObject {
  readonly event: RelationalField<'Event'>;

  title: string;
  photo_count: number;
  photos: PhotoPair[];
}

interface PhotoPair {
  original: RelatedFile;
  thumbnail: RelatedFile | null;
}
