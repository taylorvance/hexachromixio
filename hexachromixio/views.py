from django.shortcuts import render

from django.forms import ModelForm
from hexachromix.models import Game

from django import forms
from django import template
register = template.Library()


def home(request):
    variants = []
    for variant in Game.Variant:
        num = len(variant.label.split())
        variants.append({
            'label': variant.label,
            'value': variant.value,
            'teams': num,
        })

    return render(request, 'home.html', {'variants': variants})
