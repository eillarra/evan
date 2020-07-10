from evan.functions import send_task


class TemplateEmail:
    template = ""
    from_email = "Ghent University <evan@ugent.be>"

    def __init__(self, *args, instance, **kwargs) -> None:
        self.instance = instance

    @property
    def data(self):
        return (
            self.template,
            self.get_subject(),
            self.from_email,
            self.get_to_emails(),
            self.get_context_data(),
        )

    def send(self) -> None:
        send_task("evan.tasks.emails.send_template_email", self.data)
