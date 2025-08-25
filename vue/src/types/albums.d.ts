interface Album extends ApiObject {
  readonly event: RelationalField<'Event'>;

  title: string;
  photo_count: number;
  photos: PhotoPair[];
  collection_zip: RelatedFile | null;
}

interface PhotoPair {
  original: RelatedFile;
  thumbnail: RelatedFile | null;
}
