from .views import dashboard, helpers, admin, import_players

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

    path('session/<uuid:uuid>/court/<int:court_id>/', 
     dashboard.single_court, 
     name='single_court'),

    # admin
    path("session/<uuid:uuid>/admin/players/", admin.admin_players, name="admin_players"),

    path(
        "session/<uuid:uuid>/add-player-to-session/",
        helpers.add_player_to_session,
        name="add_player_to_session",
    ),

    path(
        "session/<uuid:uuid>/pause-player-in-pause/<int:player_id>/",
        helpers.pause_player_in_session,
        name="pause_player_in_session",
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

    path(
        "session/<uuid:uuid>/add-court/",
        helpers.add_court,
        name="add_court",
    ),
    path(
        "session/<uuid:uuid>/release-court/<int:court_id>/",
        helpers.release_court,
        name="release_court",
    ),

    path('import-players/', import_players.load_players_page, name='import-players'),
]