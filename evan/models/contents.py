from django.db import models


class Content(models.Model):
    """
    Contents are used to manage page contents for dedicated web pages.
    """
    event = models.ForeignKey('evan.Event', related_name='contents', on_delete=models.CASCADE)
    key = models.CharField(max_length=32)
    value = models.TextField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['event', 'key']),
        ]
        ordering = ('event', 'key')

    def __str__(self) -> str:
        return self.key
