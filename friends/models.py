from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class FriendRequest(models.Model):
    class Status(models.IntegerChoices):
        NO = 0, _('Rejected')
        YES = 1, _('Accepted')
        __empty__ = _('Pending')

    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='friend_requesters')
    responder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='friend_responders')
    status = models.IntegerField(choices=Status.choices, null=True)
    datetime_requested = models.DateTimeField(auto_now_add=True)
    datetime_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['requester', 'responder']
