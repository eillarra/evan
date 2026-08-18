type ApiEndpoint = string;
type Url = string;
type MarkdownText = string;

type CountryCode = string;

interface CountryDict {
  code: CountryCode;
  name: string;
}

interface ApiObject {
  readonly id: number;
  readonly self: ApiEndpoint;
}

interface DjangoAuthenticatedUser {
  readonly id: number;
  readonly username: string;
  readonly email: string;
  readonly first_name: string;
  readonly last_name: string;
  readonly affiliation: string;
  readonly country: string;
  readonly is_staff: boolean;
  readonly is_active: boolean;
  readonly is_superuser: boolean;
  readonly date_joined: string;
  readonly last_login: string;
}
