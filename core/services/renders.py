from .permissions import is_admin
from ..models import Session, Player, PlayerSession, UpcomingMatch, Pair, ClubConfig, GenderPair

import os

from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.utils.safestring import mark_safe


def render_courts(request, session):

    courts = session.courts.all().order_by("number")

    return {
        "club_name": ClubConfig.get("club_name", "WBT"),
        "session": session,
        "court_ids": [court.id for court in courts],
        "show_admin_panel": is_admin(request.user),
    }

def render_players(session):
    players_not_in_session = Player.objects.exclude(
        playersession__session=session
    ).distinct().order_by("name")
    
    return {
        "session": session,
        "players_not_in_session": players_not_in_session,
    }


def render_single_court(request, session, court):
    # Adapt this based on your existing render_players / court_board logic
    match = court.matches.filter(finished=False).first()
    upcoming_match = UpcomingMatch.objects.filter(
        session=session
    ).first()


    team1 = []
    team2 = []

    show_timer = False
    elapsed_seconds = 0

    if match and match.started_at:
        elapsed_seconds = int((timezone.now() - match.started_at).total_seconds())
        show_timer = elapsed_seconds < 20 * 60

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
        'active': court.active,
        'show_admin_panel': is_admin(request.user),
        "upcoming_match_id": upcoming_match.id if upcoming_match else None,
        'show_timer': show_timer,
        'elapsed_seconds': elapsed_seconds,
    }


def render_upcoming_match(request, session, upcoming_match):
    if not upcoming_match:
        return {
            "session": session,
            "upcoming_match": False,
            "show_admin_panel": is_admin(request.user),
        }

    upcoming_player_ids = [int(x) for x in upcoming_match.player_ids.split(",")]

    players = Player.objects.filter(id__in=upcoming_player_ids)
    players_map = {p.id: p for p in players}

    missing_ids = [pid for pid in upcoming_player_ids if pid not in players_map]

    if missing_ids:
        
        return {
            "session": session,
            "upcoming_match": False,
            "show_admin_panel": is_admin(request.user),
        }

    return {
        "player1": players_map[upcoming_player_ids[0]],
        "player2": players_map[upcoming_player_ids[1]],
        "player3": players_map[upcoming_player_ids[2]],
        "player4": players_map[upcoming_player_ids[3]],
        "upcoming_match": True,
        "upcoming_match_id": upcoming_match.id,
        "show_admin_panel": is_admin(request.user),
        "session": session,
        "value": upcoming_match.value,
    }


def render_pairs(session):
    # Normal pairs
    pairs = Pair.objects.filter(session=session).select_related(
        "player1_s__player",
        "player2_s__player",
    )

    # Gender pairs
    gender_pairs = GenderPair.objects.filter(session=session).select_related(
        "player1_s__player"
    )

    # IDs used in normal pairs
    pair_ids = Pair.objects.filter(session=session).values_list(
        "player1_s_id",
        "player2_s_id",
    )

    # IDs used in gender pairs
    gender_pair_ids = GenderPair.objects.filter(session=session).values_list(
        "player1_s_id",
        flat=True,
    )

    paired_ids = {
        *{pid for pair in pair_ids for pid in pair},
        *gender_pair_ids,
    }

    # Players available for normal pairs
    player_sessions_not_paired = (
        session.playersession_set
        .select_related("player")
        .exclude(id__in=paired_ids)
        .filter(pause=False)
        .order_by("player__name")
    )

    player_sessions_not_paired_and_gender = [
        {
            "type": "gender",
            "value": "M",
            "display": "MEN_ONLY",
        },
        {
            "type": "gender",
            "value": "F",
            "display": "WOMEN_ONLY",
        },
    ]

    player_sessions_not_paired_and_gender += [
        {
            "type": "player",
            "object": ps,
        }
        for ps in player_sessions_not_paired
    ]

    

    return {
        "pairs": pairs,
        "gender_pairs": gender_pairs,
        "player_sessions_not_paired": player_sessions_not_paired,
        "player_sessions_not_paired_and_gender": player_sessions_not_paired_and_gender,
        "session": session,
    }


def render_switch_players(session):

    session_players = Player.objects.filter(
        playersession__session=session
    ).distinct()

    in_match_players = Player.objects.filter(
        matchparticipant__match_team__match__court__session=session,
        matchparticipant__match_team__match__finished=False
    ).distinct()

    in_match_ids = in_match_players.values_list("id", flat=True)

    upcoming_match = UpcomingMatch.objects.filter(
            session=session
        ).order_by("-value").first()

    if upcoming_match:
        upcoming_player_ids = [int(x) for x in upcoming_match.player_ids.split(",")]
        upcoming_players = Player.objects.filter(id__in=upcoming_player_ids)
        upcoming_ids = upcoming_players.values_list("id", flat=True)

        in_match_or_upcoming_player_ids = set(in_match_ids) | set(upcoming_ids)
    else:
        in_match_or_upcoming_player_ids = in_match_ids


    in_match_or_upcoming_players = session_players.filter(
        id__in=in_match_or_upcoming_player_ids
    )

    waiting_and_not_in_upcoming_players = session_players.exclude(
        id__in=in_match_or_upcoming_player_ids
    ).filter(
        playersession__pause=False,
    )


    return {
        'in_match_or_upcoming_players': in_match_or_upcoming_players,
        'waiting_and_not_in_upcoming_players': waiting_and_not_in_upcoming_players,
        'session': session, 
    }

def waiting_players(request, uuid):
    session = get_object_or_404(Session, uuid=uuid)

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
            "name_played": mark_safe(
                f"{Player.format_name_gender(ps.player.name, ps.player.gender == 'F')}<sup>{ps.player.mu}  {ps.games_played}|{ps.games_skipped + ps.games_played}</sup>"
            ),
        }
        for ps in player_sessions
    ], key=lambda p: (p["name"].lower()))
    

    return render(request, "match/partials/waiting_list.html", {
        "players": players_waiting_dict,
        "session": session,
    })

def paused_players(request, uuid):
    session = get_object_or_404(Session, uuid=uuid)

    players = Player.objects.filter(
        playersession__session=session,
        playersession__pause=True
    )

    return render(request, "match/partials/paused_list.html", {
        "players": players,
        "session": session,
    })