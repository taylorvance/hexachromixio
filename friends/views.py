from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

from friends.models import FriendRequest


@login_required
def request_friend(request):
    User = get_user_model()

    users = User.objects.filter(username__iexact=request.POST['name']).exclude(pk=request.user.pk)
    if len(users) == 0:
        users = User.objects.filter(username__icontains=request.POST['name']).exclude(pk=request.user.pk)

    if len(users) == 0:
        #.msg none found
        pass
    elif len(users) == 1:
        other_user = users.first()

        # If the friend has already made a request, accept it
        fr = FriendRequest.objects.filter(requester=other_user, responder=request.user).first()
        if fr:
            fr.status = FriendRequest.Status.YES
            fr.save()
        else:
            # Else, make a request
            FriendRequest.objects.get_or_create(requester=request.user, responder=other_user)
    elif len(friends) > 1:
        #.show options
        pass

    return redirect('/account/profile')

@login_required
def remove_friend(request):
    fr = FriendRequest.request_between_users(request.user, request.POST['upk'])
    if fr:
        fr.delete()
    return redirect('/account/profile')

@login_required
def accept_request(request):
    fr = FriendRequest.objects.get(pk=request.POST['frpk'], responder=request.user)
    fr.status = FriendRequest.Status.YES
    fr.save()
    return redirect('/account/profile')
@login_required
def decline_request(request):
    fr = FriendRequest.objects.get(pk=request.POST['frpk'], responder=request.user)
    fr.status = FriendRequest.Status.NO
    fr.save()
    return redirect('/account/profile')

@login_required
def cancel_request(request):
    FriendRequest.objects.get(pk=request.POST['frpk'], requester=request.user).delete()
    return redirect('/account/profile')
