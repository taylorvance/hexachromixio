from django.shortcuts import render
from django.http import HttpResponse

def landing_page(request):
    return render(request, 'hexachromix/landing_page.html')
