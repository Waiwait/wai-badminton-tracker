from django.contrib import admin
from .models import Player, Session, PlayerSession, Court, MatchmakingConfig, ClubConfig

from django.urls import reverse
from django.utils.html import format_html

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("name", "gender", "mu", "sigma")
    list_filter = ("gender",)
    search_fields = ("name",)
    ordering = ("-mu",)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "venue", "active", "session_link", "session_summary")
    list_filter = ("active",)
    ordering = ("-date",)

    def session_link(self, obj):
        url = reverse("session_detail", kwargs={"uuid": obj.uuid})
        return format_html('<a href="{}" target="_blank">Open Link</a>', url)
    

    def session_summary(self, obj):
        url = reverse("session_summary", kwargs={"uuid": obj.uuid})
        return format_html('<a href="{}" target="_blank">Open Link</a>', url)

    session_link.short_description = "Dashboard"
    session_summary.short_description = "Summary"


@admin.register(PlayerSession)
class PlayerSessionAdmin(admin.ModelAdmin):
    list_display = ("session", "player", "pause")
    list_filter = ("pause",)


@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ("number", "session")
    list_filter = ("session",)
    ordering = ("session", "number")


@admin.register(MatchmakingConfig)
class MatchmakingConfigAdmin(admin.ModelAdmin):
    list_display = [
        'games_played_weight', 'fairness_weight', 'played_with_weight',
        'played_against_weight', 'gender_weight', 'skill_difference_weight'
    ]
    fieldsets = [
        ("Matchmaking Weights", {
            'fields': [
                'games_played_weight',
                'fairness_weight',
                'played_with_weight',
                'played_against_weight',
                'gender_weight',
                'skill_difference_weight',
            ]
        }),
    ]

    def has_add_permission(self, request):
        return False  # Prevent creating new rows

    def has_delete_permission(self, request, obj=None):
        return False  # Prevent deletion
    

@admin.register(ClubConfig)
class ClubConfig(admin.ModelAdmin):
    list_display = ("key", "value")
    list_filter = ("key",)
