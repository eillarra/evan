interface UserTiny {
  readonly username: string;
  readonly email: string;
  readonly name: string;
  readonly affiliation: string;
}

interface AuthenticatedUser extends User, ApiObject {}
