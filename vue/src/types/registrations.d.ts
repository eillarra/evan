interface CouponData {
  value: number;
  notes: string;
}

interface Coupon extends ApiObject, CouponData {
  readonly code: string;
  readonly created_at: string;
}

interface RegistrationExtraData {
  accompanying_persons?: string[];
  [key: string]: unknown;
}

interface RegistrationData {
  fee_type: string;
  extra_data: RegistrationExtraData;

  visa_requested?: boolean;
  invoice_requested?: boolean;
}

interface Registration extends RegistrationData {
  readonly self: ApiEndpoint;
  readonly url: Url;
  readonly payment_url: Url;
  readonly uuid: string;
  readonly user: UserTiny;
  readonly created_at: string;
  readonly updated_at: string;
  readonly event: EvanEvent;
  readonly coupon: Coupon | null;

  readonly visa_sent: boolean;
  readonly base_fee: number;
  readonly extra_fees: number;
  readonly manual_extra_fees: number;
  readonly invoice_sent: boolean;

  readonly paid: number;
  readonly paid_via_invoice: number;
}
