from .permissions import is_admin
from ..models import Player


def render_matches(request, session):
    courts = session.courts.all().order_by("number")

    court_data = []

    for court in courts:
        match = court.matches.filter(finished=False).first()

        team1 = []
        team2 = []

        if match: 
            for team in match.teams.all():
                if team.team_number == 1:
                    team1 = [p.player for p in team.participants.all()]
                else:
                    team2 = [p.player for p in team.participants.all()]

        court_data.append({
            "court": court,
            "active": court.active,
            "match": match if match else None,
            "team1": team1,
            "team2": team2,
        })

    return {
        "session": session,
        "court_data": court_data,
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

    players_waiting = session_players.exclude(id__in=in_match_players)

    # Players not in this session at all
    players_not_in_session = Player.objects.exclude(
        playersession__session=session
    ).distinct()

    return {
        "session": session,
        "players_waiting": players_waiting,
        "players_not_in_session": players_not_in_session,
    }
