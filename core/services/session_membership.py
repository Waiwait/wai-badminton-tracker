from ..models import PlayerSession, Player


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


def add_player(session, player):
    obj, _ = PlayerSession.objects.get_or_create(
        session=session,
        player=player
    )
    return obj


def remove_player(session, player):
    PlayerSession.objects.filter(
        session=session,
        player=player
    ).delete()