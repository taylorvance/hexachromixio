from django.shortcuts import render
from django.http import HttpResponse


def landing_page(request):
    return render(request, 'hexachromix/landing_page.html')

def create_or_join(request):
    return HttpResponse("creating game "+request.POST['game_name'])
