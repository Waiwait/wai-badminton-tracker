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


    path('session/<uuid:uuid>/upcoming-match/', 
     dashboard.upcoming_match, 
     name='upcoming_match'),

    # admin
    path("session/<uuid:uuid>/admin/players/", admin.admin_players, name="admin_players"),
    path("session/<uuid:uuid>/admin/pairs/", admin.admin_pairs, name="admin_pairs"),
    path("session/<uuid:uuid>/admin/new-player/", admin.new_player, name="admin_new_player"),
    path("session/<uuid:uuid>/admin/switch-players/", admin.switch_players, name="admin_switch_players"),

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
        "session/<uuid:uuid>/generate-upcoming-match/",
        helpers.generate_upcoming_match,
        name="generate_upcoming_match",
    ),

    path(
        "session/<uuid:uuid>/add-upcoming-match-to-court/<int:court_id>/<int:upcoming_match_id>",
        helpers.add_upcoming_match_to_court,
        name="add_upcoming_match_to_court",
    ),

    path(
        "session/<uuid:uuid>/delete-upcoming-match/<int:upcoming_match_id>",
        helpers.delete_upcoming_match,
        name="delete_upcoming_match",
    ),
    path(
        "session/<uuid:uuid>/delete-upcoming-matches/",
        helpers.delete_upcoming_matches,
        name="delete_upcoming_matches",
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

    path(
        "session/<uuid:uuid>/add-pair/",
        helpers.add_pair,
        name="add_pair",
    ),

    path(
        "session/<uuid:uuid>/delete-pair/<int:pair_id>/",
        helpers.delete_pair,
        name="delete_pair",
    ),
    
    path(
        "session/<uuid:uuid>/add-new-player/",
        helpers.add_new_player,
        name="add_new_player",
    ),

    path(
        "session/<uuid:uuid>/switch-players/",
        helpers.switch_players,
        name="switch_players",
    ),

    path('import-players/', import_players.load_players_page, name='import-players'),
]