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
