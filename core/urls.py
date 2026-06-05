from .views import dashboard, helpers

from django.urls import path


urlpatterns = [
    path("session/<uuid:uuid>/", dashboard.session_detail, name="session_detail"),
    path("manage/session/<uuid:uuid>/", dashboard.session_control_panel, name="session_control"),
    path(
        "manage/session/<uuid:session_uuid>/add-player/",
        helpers.add_player,
        name="add_player",
    ),
    path(
        "manage/session/<uuid:session_uuid>/add-player/",
        helpers.add_player,
        name="add_player",
    ),
]