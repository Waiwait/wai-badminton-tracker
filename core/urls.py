from .views import dashboard, helpers, admin

from django.urls import path


urlpatterns = [
    path("session/<uuid:uuid>/", dashboard.session_detail, name="session_detail"),

    # board
    path("session/<uuid:uuid>/board/", helpers.court_board, name="court_board"),

    # admin
    path("session/<uuid:uuid>/admin/dashboard/", dashboard.admin_dashboard, name="admin_dashboard"),
    path("session/<uuid:uuid>/admin/players/", admin.admin_players, name="admin_players"),

    path(
        "session/<uuid:uuid>/add-player-to-session/",
        helpers.add_player_to_session,
        name="add_player_to_session",
    ),
    path(
        "session/<uuid:uuid>/remove-player-from-session/<int:player_id>/",
        helpers.remove_player_from_session,
        name="remove_player_from_session",
    ),
]