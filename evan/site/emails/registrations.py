from typing import List

from .generic import TemplateEmail


class RegistrationEmail(TemplateEmail):
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
            "invoice_requested": obj.invoice_requested,
            "registrations_count": obj.event.registrations_count,
            "registration_uuid": str(obj.uuid),
            "registration_url": obj.get_absolute_url(),
            "payment_url": obj.get_payment_url(),
            "payment_delegated_url": obj.get_payment_delegated_url(),
        }


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
