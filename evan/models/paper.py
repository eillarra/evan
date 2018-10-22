from django.db import models


class Paper(models.Model):
    event = models.ForeignKey('evan.Event', related_name='papers', on_delete=models.CASCADE)
    title = models.TextField()
    authors = models.TextField()

    def __str__(self) -> str:
        return self.title
