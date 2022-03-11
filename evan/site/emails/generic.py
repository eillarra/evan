from datetime import datetime, timedelta

from evan.tasks.emails import send_template_email


class TemplateEmail:
    template = ""
    from_email = "Ghent University <evan@ugent.be>"

    def __init__(self, *args, instance=None, queryset=None, **kwargs) -> None:
        self.queryset = queryset
        self.instance = instance

    def get_from_email(self, obj) -> str:
        return self.from_email

    def get_data(self, obj) -> tuple:
        return (
            self.template,
            self.get_subject(obj),
            self.get_from_email(obj),
            self.get_to_emails(obj),
            self.get_context_data(obj),
        )

    def send(self) -> None:
        if self.instance:
            send_template_email(*self.get_data(self.instance))

        if self.queryset:
            eta = datetime.now()
            for instance in self.queryset:
                send_template_email.schedule(self.get_data(instance), eta=eta)
                eta = eta + timedelta(seconds=25)
