from typing import List

from .generic import TemplateEmail


class RegistrationEmail(TemplateEmail):
    def get_to_emails(self) -> List[str]:
        return [self.instance.user.email]

    def get_context_data(self):
        return {
            "user_name": self.instance.user.profile.name,
            "event_name": self.instance.event.name,
            "event_city": self.instance.event.city,
            "event_url": self.instance.event.get_absolute_url(),
            "registrations_count": self.instance.event.registrations_count,
            "registration_uuid": str(self.instance.uuid),
            "registration_url": self.instance.get_absolute_url(),
            "payment_url": self.instance.get_payment_url(),
        }


class RegistrationReminderEmail(RegistrationEmail):
    template = "_emails/registrations_reminder.md.html"

    def get_subject(self) -> str:
        return f"[{self.instance.event.hashtag}] Please update your registration / {self.instance.uuid}"


class PaymentReminderEmail(RegistrationEmail):
    template = "_emails/registrations_payment_reminder.md.html"

    def get_subject(self) -> str:
        return f"[{self.instance.event.hashtag}] Payment reminder / {self.instance.uuid}"


class VisaReminderEmail(RegistrationEmail):
    template = "_emails/registrations_visa_reminder.md.html"

    def get_subject(self) -> str:
        return f"[{self.instance.event.hashtag}] Your visa application / {self.instance.uuid}"
