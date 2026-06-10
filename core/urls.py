from .views import dashboard, helpers, admin

from django.urls import path


urlpatterns = [
    path("session/<uuid:uuid>/", dashboard.session_detail, name="session_detail"),

    # board
    path("session/<uuid:uuid>/board/", dashboard.court_board, name="court_board"),

    path(
        "session/<uuid:uuid>/session-history",
        dashboard.session_history,
        name="session_history",
    ),

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

    path(
        "session/<uuid:uuid>/generate-match/<int:court_id>/",
        helpers.generate_match,
        name="generate_match",
    ),
    path(
        "session/<uuid:uuid>/finish-match/<int:match_id>/",
        helpers.finish_match,
        name="finish_match",
    ),
]