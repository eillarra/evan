interface Remark extends ApiObject {
  self: ApiEndpoint;
  text: string;
  created_at: string;
  created_by: UserTiny;
  // -----
  is_mine?: boolean;
  stamp?: string;
}
