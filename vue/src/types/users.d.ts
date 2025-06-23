type DietaryOption = 'none' | 'vegetarian' | 'vegan' | 'gluten_free' | 'dairy_free' | 'nut_free' | 'other';

interface UserExtraData {
  gender: import('../utils/gender').GenderOption;
  dietary: DietaryOption;
  special_needs: string | null;
  connect: boolean;
}

interface UserData {
  first_name: string;
  last_name: string;
  affiliation: string;
  country: CountryCode;
  extra_data: UserExtraData;
}

interface UserTiny {
  readonly id: number;
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
