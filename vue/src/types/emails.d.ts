type EmailAddress = string;

interface Email extends ApiObject {
  sent_at: string;
  subject: string;
  to: EmailAddress[];
  bcc: EmailAddress[];
  reply_to: EmailAddress[];
  tags: Tags;

  _tags_dict?: TagsDict;
}

interface FullEmail extends Email {
  body: string;
  registration: Registration;
}

interface EmailPlanFilters {
  fee_types: string[];
  sessions: { ids: number[]; match: 'all' | 'any' };
  session_days: string[];
  payment_status: 'paid' | 'unpaid' | null;
}

interface EmailPlan extends ApiObject {
  name: string;
  subject: string;
  body: string;
  from_email: string;
  bcc_email: string;
  reply_to_email: string;
  filters: EmailPlanFilters;
  send_at: string | null;
  created_by?: string;
  created_at: string;
  updated_at: string;
  recipients_count: number;
}
