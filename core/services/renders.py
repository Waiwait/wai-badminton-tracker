from .permissions import is_admin
from ..models import Player, PlayerSession

from django.utils.safestring import mark_safe


def render_courts(request, session):
    courts = session.courts.all().order_by("number")

    return {
        "session": session,
        "court_ids": [court.id for court in courts],
        "show_admin_panel": is_admin(request.user),
    }

def render_players(session):
    # All players registered in this session
    session_players = Player.objects.filter(
        playersession__session=session
    ).distinct()

    # Players currently in a match in this session
    in_match_players = Player.objects.filter(
        matchparticipant__match_team__match__court__session=session,
        matchparticipant__match_team__match__finished=False
    ).distinct()
    

    players_waiting = session_players.exclude(id__in=in_match_players).filter(
        playersession__session=session,
        playersession__pause=False)

    player_sessions = PlayerSession.objects.filter(
    session=session,
    player__in=players_waiting,).select_related("player")

    players_waiting_dict = sorted([
        {
            "id": ps.player.id,
            "name": ps.player.name,
            "name_played": mark_safe(f"{Player.format_name_gender(ps.player.name, ps.player.gender == "F")}<sup>{ps.games_played}|{ps.games_skipped + ps.games_played}</sup>"),
        }
        for ps in player_sessions
    ], key=lambda p: (p["name"].lower()))

    # Players not in this session at all
    players_paused = Player.objects.filter(
        playersession__pause=True,
        playersession__session=session,
    ).distinct()

    players_not_in_session = Player.objects.exclude(
        playersession__session=session
    ).distinct().order_by("name")

    combined = players_paused | players_not_in_session
    combined = combined.distinct()
    
    return {
        "session": session,
        "players_waiting": players_waiting_dict,
        "players_not_in_session_or_paused": combined,
    }


def render_single_court(request, session, court):
    # Adapt this based on your existing render_players / court_board logic
    match = court.matches.filter(finished=False).first()

    team1 = []
    team2 = []

    if match: 
        for team in match.teams.all():
            if team.team_number == 1:
                team1 = [p.player for p in team.participants.all()]
            else:
                team2 = [p.player for p in team.participants.all()]

    return {
        'session': session,
        'court': court,
        'match': match,
        "team1": team1,
        "team2": team2,
        'active': court.active,   # adjust as needed
        'show_admin_panel': is_admin(request.user), # or pass from view
    }