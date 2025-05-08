interface TopicData {
  name: string;
}

interface Topic extends ApiObject, TopicData {
  slug?: string;
}

interface TrackData {
  name: string;
  position?: number;
}

interface Track extends ApiObject, TrackData {
  slug?: string;
}
