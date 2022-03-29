from typing import List

from .generic import TemplateEmail


class RegistrationEmail(TemplateEmail):
    def get_from_email(self, obj) -> str:
        if obj.event.email:
            return f"{obj.event.name} <{obj.event.email}>"
        return self.from_email

    @staticmethod
    def get_to_emails(obj) -> List[str]:
        return [obj.user.email]

    @staticmethod
    def get_context_data(obj):
        return {
            "user_name": obj.user.profile.name,
            "event_allows_invoices": obj.event.allows_invoices,
            "event_name": obj.event.name,
            "event_city": obj.event.city,
            "event_url": obj.event.get_absolute_url(),
            "event_email": obj.event.email if obj.event.email else "evan@ugent.be",
            "registrations_count": obj.event.registrations_count,
            "registration_uuid": str(obj.uuid),
            "registration_url": obj.get_absolute_url(),
            "invoice_requested": obj.invoice_requested,
            "visa_requested": obj.visa_requested,
            "payment_url": obj.get_payment_url(),
            "payment_delegated_url": obj.get_payment_delegated_url(),
        }


class RegistrationCreatedEmail(RegistrationEmail):
    template = "_emails/registrations_created.md.html"

    @staticmethod
    def get_subject(obj) -> str:
        return f"[{obj.event.hashtag}] Your registration / {obj.uuid}"


class RegistrationProfileReminderEmail(RegistrationEmail):
    template = "_emails/registrations_profile_update_reminder.md.html"

    @staticmethod
    def get_subject(obj) -> str:
        return f"[{obj.event.hashtag}] Please update your profile / {obj.uuid}"


class RegistrationReminderEmail(RegistrationEmail):
    template = "_emails/registrations_reminder.md.html"

    @staticmethod
    def get_subject(obj) -> str:
        return f"[{obj.event.hashtag}] Please update your registration / {obj.uuid}"


class DelegatedPaymentEmail(RegistrationEmail):
    template = "_emails/registrations_delegated_payment.md.html"

    @staticmethod
    def get_subject(obj) -> str:
        return f"[{obj.event.hashtag}] Payment link / {obj.uuid}"


class PaymentReminderEmail(RegistrationEmail):
    template = "_emails/registrations_payment_reminder.md.html"

    @staticmethod
    def get_subject(obj) -> str:
        return f"[{obj.event.hashtag}] Payment reminder / {obj.uuid}"


class VisaReminderEmail(RegistrationEmail):
    template = "_emails/registrations_visa_reminder.md.html"

    @staticmethod
    def get_subject(obj) -> str:
        return f"[{obj.event.hashtag}] Your visa application / {obj.uuid}"
