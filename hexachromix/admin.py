from django.contrib import admin

from .models import Game, Move

class GameAdmin(admin.ModelAdmin):
    readonly_fields=['datetime_created', 'uid', 'code']

class MoveAdmin(admin.ModelAdmin):
    readonly_fields=['datetime_created']

admin.site.register(Game, GameAdmin)
admin.site.register(Move, MoveAdmin)
