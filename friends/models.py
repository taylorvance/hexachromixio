from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.contrib.auth import get_user_model


class FriendRequest(models.Model):
    class Status(models.IntegerChoices):
        NO = 0, _('Declined')
        YES = 1, _('Accepted')
        __empty__ = _('Pending')

    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='friend_requesters')
    responder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='friend_responders')
    status = models.IntegerField(choices=Status.choices, null=True)
    datetime_requested = models.DateTimeField(auto_now_add=True)
    datetime_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['requester', 'responder']

    @staticmethod
    def pending_requests_to_user(user):
        return user.friend_responders.filter(status__isnull=True)

    @staticmethod
    def pending_requests_from_user(user):
        return user.friend_requesters.filter(status__isnull=True)

    @staticmethod
    def request_between_users(user1, user2):
        return FriendRequest.objects.filter((Q(requester=user1) & Q(responder=user2)) | (Q(requester=user2) & Q(responder=user1))).first()


# Extend the User model with a helper method to get friends
def friends(self):
    friends = []
    for fr in self.friend_requesters.filter(status=FriendRequest.Status.YES):
        friends.append(fr.responder)
    for fr in self.friend_responders.filter(status=FriendRequest.Status.YES):
        friends.append(fr.requester)
    friends = sorted(friends, key=lambda x: x.username)
    return friends
get_user_model().add_to_class('friends', friends)
