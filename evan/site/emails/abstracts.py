from .generic import TemplateEmail


class AbstractEmail(TemplateEmail):
    def get_from_email(self, obj) -> str:
        if obj.event.email:
            return f"{obj.event.name} <{obj.event.email}>"
        return self.from_email

    @staticmethod
    def get_to_emails(obj) -> list[str]:
        return [obj.user.email]

    @staticmethod
    def get_context_data(obj):
        return {
            "user_name": obj.user.profile.name,
            "event_name": obj.event.name,
            "event_city": obj.event.city,
            "event_url": obj.event.get_absolute_url(),
            "abstract_url": obj.get_absolute_url(),
        }


class AbstractCreatedEmail(AbstractEmail):
    template = "_emails/abstracts_created.md.html"

    @staticmethod
    def get_subject(obj) -> str:
        return f"[#{obj.event.hashtag}] Your abstract submission / {obj.uuid}"
