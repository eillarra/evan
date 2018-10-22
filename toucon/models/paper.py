from django.db import models


class Paper(models.Model):
    conference = models.ForeignKey('toucon.Conference', related_name='papers', on_delete=models.CASCADE)
    title = models.TextField()
    authors = models.TextField()

    def __str__(self) -> str:
        return self.title
