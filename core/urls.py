from .views import dashboard, helpers

from django.urls import path


urlpatterns = [
    path("session/<uuid:uuid>/", dashboard.session_detail, name="session_detail"),
    path("manage/session/<uuid:uuid>/", dashboard.session_control_panel, name="session_control"),
    path("session/<uuid:uuid>/board/", helpers.court_board, name="court-board"),
    path(
        "manage/session/<uuid:session_uuid>/add-player/",
        helpers.add_player,
        name="add_player",
    ),
    path(
        "maange/session/<uuid:session_uuid>/add-player/",
        helpers.add_player,
        name="add_player",
    ),
]