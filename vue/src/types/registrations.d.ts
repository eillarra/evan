interface CouponData {
  value: number;
  notes: string;
  coverage: 'base_fee' | 'all_fees';
}

interface Coupon extends ApiObject, CouponData {
  readonly code: string;
  readonly created_at: string;
}

interface AccompanyingPerson {
  name: string;
  dietary: DietaryOption;
  selected_social_events: number[];
}

interface RegistrationExtraDataInternal {
  share_email_with_sponsors?: boolean;
  allow_photo_sharing?: boolean;
}

interface RegistrationExtraData {
  _internal?: RegistrationExtraDataInternal;
  accompanying_persons?: AccompanyingPerson[];
  [key: string]: unknown;
}

interface RegistrationData {
  fee_type: string;
  extra_data: RegistrationExtraData;
  sessions: number[];

  visa_requested?: boolean;
  invoice_requested?: boolean;
}

interface Registration extends RegistrationData {
  readonly self: ApiEndpoint;
  readonly rel_remarks: ApiEndpoint;

  readonly is_early: boolean;
  readonly url: Url;
  readonly payment_url: Url;
  readonly receipt_url: Url;
  readonly certificate_url: Url;
  readonly uuid: string;
  readonly user: UserTiny;
  readonly created_at: string;
  readonly updated_at: string;
  readonly event: EvanEvent;
  readonly coupon: Coupon | null;

  readonly visa_sent: boolean;
  readonly total_fee: number;
  readonly base_fee: number;
  readonly extra_fees: number;
  readonly manual_extra_fees: number;
  readonly invoice_sent: boolean;

  readonly paid: number;
  readonly paid_via_invoice: number;
  readonly saldo: number;
  readonly is_paid: boolean;

  readonly is_accepted: boolean | null;
  readonly no_show: boolean;

  readonly tags: Tags;

  _tags_dict?: TagsDict;
}
