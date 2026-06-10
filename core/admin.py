from django.contrib import admin
from .models import Player, Session, PlayerSession, Match, MatchParticipant, Court

from django.urls import reverse
from django.utils.html import format_html

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("name", "gender", "mu")
    list_filter = ("gender",)
    search_fields = ("name",)
    ordering = ("-mu",)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "venue", "active", "session_link")
    list_filter = ("active",)
    ordering = ("-date",)

    def session_link(self, obj):
        url = reverse("session_detail", kwargs={"uuid": obj.uuid})
        return format_html('<a href="{}" target="_blank">Open Link</a>', url)

    session_link.short_description = "Public Link"


@admin.register(PlayerSession)
class PlayerSessionAdmin(admin.ModelAdmin):
    list_display = ("session", "player", "pause")
    list_filter = ("pause",)


@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ("number", "session")
    list_filter = ("session",)
    ordering = ("session", "number")