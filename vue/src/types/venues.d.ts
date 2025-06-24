interface VenueData {
  name: string;
  city: string;
  presentation: string;
  is_main: boolean;
  website: string;
  google_place_id: string;
}

interface RoomData {
  name: string;
  max_capacity: number;
  position: number;
  venue: number;
}

interface Room extends ApiObject {
  name: string;
  max_capacity: number;
  position: number;
  venue?: number;
}

interface Venue extends ApiObject {
  name: string;
  city: string;
  presentation: MarkdownText;
  is_main: boolean;
  website: string;
  google_place_id: string;
  rooms: Room[];
}
