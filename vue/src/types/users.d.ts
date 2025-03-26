type DietaryOption =
  | 'none'
  | 'vegetarian'
  | 'vegan'
  | 'kosher'
  | 'halal'
  | 'gluten_free'
  | 'dairy_free'
  | 'nut_free'
  | 'other';

interface UserExtraData {
  gender: string;
  dietary: DietaryOption;
  special_needs: string | null;
  connect: boolean;
}

interface UserData {
  first_name: string;
  last_name: string;
  affiliation: string;
  country: string;
  extra_data: UserExtraData;
}

interface UserTiny {
  readonly username: string;
  readonly email: string;
  readonly name: string;
  readonly affiliation: string;
}

interface AuthenticatedUser extends UserData, ApiObject {
  readonly email: string;
  readonly first_name: string;
  readonly last_name: string;
}
