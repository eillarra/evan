interface CouponCreateData {
  value: number;
  notes: string;
}

interface Coupon extends ApiObject, CouponCreateData {
  readonly code: string;

  created_at: string;
}

interface RegistrationExtraData {
  accompanying_persons: string[];
}

interface Registration {
  readonly url: Url;
  readonly payment_url: Url;
  readonly uuid: string;
  readonly user: UserTiny;
  readonly created_at: string;
  readonly updated_at: string;

  extra_data: RegistrationExtraData;
  coupon: Coupon | null;
}
