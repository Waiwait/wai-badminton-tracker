
from ..models import Session, Player, Match, Court, MatchTeam, MatchParticipant, PlayerSession, UpcomingMatch
from ..services.permissions import is_admin
from ..services.session_membership import add_player, remove_player
from ..services.openskill import score_match
from ..services.matchmaking import matchmaking
from ..services.match_state import is_cancelled_game

import json

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db import models


@user_passes_test(is_admin)
def add_player_to_session(request, uuid):
    session = get_object_or_404(Session, uuid=uuid)
    player = get_object_or_404(Player, id=request.POST["player_id"])


    player_session, created = PlayerSession.objects.get_or_create(
        session=session,
        player=player,
    )

    if not created:
        player_session.pause = False
        player_session.save(update_fields=["pause"])

    response = HttpResponse("ok")
    response["HX-Trigger"] = json.dumps({
        "players_update": True
    })
    return response


@user_passes_test(is_admin)
def pause_player_in_session(request, uuid, player_id):
    session = get_object_or_404(Session, uuid=uuid)
    player = get_object_or_404(Player, id=player_id)

    PlayerSession.objects.filter(
        session=session,
        player=player
    ).update(pause=True)

    response = HttpResponse("ok")
    response["HX-Trigger"] = json.dumps({
        "players_update": True
    })
    return response


@user_passes_test(is_admin)
def finish_match(request, uuid, match_id):
    session = get_object_or_404(Session, uuid=uuid)
    
    match = get_object_or_404(
        Match, 
        id=match_id, 
        court__session=session
    )

    team1_score = int(request.POST.get('team1_score', 0))
    team2_score = int(request.POST.get('team2_score', 0))

    # Get both teams
    team1 = match.teams.get(team_number=1)
    team2 = match.teams.get(team_number=2)

    # Update scores
    team1.score = team1_score
    team2.score = team2_score

    cancelled_game = is_cancelled_game(team1_score, team2_score)

    # Determine winner
    if cancelled_game:
        team1.is_winner = False
        team2.is_winner = False
    elif team1_score > team2_score:
        team1.is_winner = True
        team2.is_winner = False
    elif team2_score > team1_score:
        team1.is_winner = False
        team2.is_winner = True
    else:
        team1.is_winner = False
        team2.is_winner = False

    team1.save()
    team2.save()

    match.finished = True
    match.save()
    
    if not cancelled_game:
        try:
            score_match(match)
        except Exception as e:
            messages.warning(
                request, 
                f"Match on Court {match.court.number} finished! Could not score match: {e}"
            )

    if not cancelled_game:
        # Update games_played / games_skipped
        played_players = set()
        for team in [team1, team2]:
            for participant in team.participants.all():
                played_players.add(participant.player_id)

        player_sessions = PlayerSession.objects.filter(
            session=session,
            pause=False
        )

        updates = []
        for ps in player_sessions:
            if ps.player_id in played_players:
                ps.games_played = models.F('games_played') + 1
            else:
                ps.games_skipped = models.F('games_skipped') + 1
            updates.append(ps)

        if updates:
            PlayerSession.objects.bulk_update(updates, ['games_played', 'games_skipped'])

    messages.success(
        request, 
        f"Match on Court {match.court.number} finished! Score: {team1_score} - {team2_score}"
    )
    
    response = HttpResponse("ok")
    response["HX-Trigger"] = json.dumps({
        "players_update": True,
        f"court_{match.court.id}_update": True,
        "history_update": True,
    })
    return response

@user_passes_test(is_admin)
def generate_match(request, uuid, court_id):
    session = get_object_or_404(Session, uuid=uuid)
    
    court = get_object_or_404(
        Court, 
        id=court_id, 
        session=session
    )

    existing_match = court.matches.filter(finished=False).first()
    
    if existing_match:
        existing_match.finished = True
        existing_match.save()
        messages.warning(
            request, 
            f"Previous match on Court {court.number} was closed."
        )

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
    playersession__pause=False,
    playersession__session=session,
)

    # Need at least 4 players
    if len(players_waiting) < 4:
        messages.error(request, "Not enough players waiting (need at least 4)")
        return render(request, "match/session_dashboard.html", {
        "session": session,
        "show_admin_panel": is_admin(request.user),
    })
    
    matches_ranked = matchmaking(players_waiting=players_waiting, session=session)
    match_chosen = matches_ranked[0]

    
    # Create new Match
    match = Match.objects.create(court=court)

    # Create two teams
    team1 = MatchTeam.objects.create(match=match, team_number=1)
    team2 = MatchTeam.objects.create(match=match, team_number=2)

    def create_player(player_id, team):
        player = Player.objects.get(id=player_id)
        MatchParticipant.objects.create(
            match_team=team,
            player=player
        )
    # Assign 2 players to each team
    create_player(match_chosen["teams"][0][0]["id"], team1)
    create_player(match_chosen["teams"][0][1]["id"], team1)
    create_player(match_chosen["teams"][1][0]["id"], team2)
    create_player(match_chosen["teams"][1][1]["id"], team2)


    messages.success(
        request, 
        f"New match started on Court {court.number}!"
    )

    response = HttpResponse("ok")
    response["HX-Trigger"] = json.dumps({
        "players_update": True,
        f"court_{match.court.id}_update": True
    })
    return response


@user_passes_test(is_admin)
def add_court(request, uuid):
    session = get_object_or_404(Session, uuid=uuid)

    # 1. Try to find an inactive court
    court = session.courts.filter(active=False).order_by("number").first()

    if court:
        court.active = True
        court.save()
    else:
        # 2. Otherwise create next court number
        last_number = session.courts.aggregate(models.Max("number"))["number__max"] or 0

        if last_number <= 3:
            court = Court.objects.create(
                session=session,
                number=last_number + 1,
                active=True
            )
        else:
            response = HttpResponse("Maximum of 4 courts allowed")
            return response

    response = HttpResponse("ok")
    response["HX-Trigger"] = json.dumps({
        "court_board_update": True,
    })
    return response


@user_passes_test(is_admin)
def release_court(request, uuid, court_id):
    session = get_object_or_404(Session, uuid=uuid)
    court = get_object_or_404(Court, id=court_id, session=session)

    # check for unfinished match
    has_active_match = court.matches.filter(finished=False).exists()

    if has_active_match:
        # don't allow deactivation

        response = HttpResponse("Cannot deactivate court: active match in progress")
        response["HX-Trigger"] = json.dumps({})
        return response

    court.active = False
    court.save()

    response = HttpResponse("ok")
    response["HX-Trigger"] = json.dumps({
        f"court_{court.id}_update": True
    })
    return response


@user_passes_test(is_admin)
def generate_upcoming_match(request, uuid):

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
    playersession__pause=False,
    playersession__session=session,
)

    # Need at least 4 players
    if players_waiting.count() < 4:
        return HttpResponse("Need 4+ waiting players to generate an upcoming game")
    

    upcoming_matches = matchmaking(players_waiting=players_waiting, session=session)

    for upcoming_match in upcoming_matches:

        p_ids = []

        for team in upcoming_match["teams"]:
            for player in team:
                p_ids.append(str(player["id"]))

        UpcomingMatch.objects.create(
            value = upcoming_match["score"],
            session = session,
            player_ids = ",".join(p_ids)
        )

    response = HttpResponse("ok")
    response["HX-Trigger"] = json.dumps({
        f"upcoming_match_update": True,
         "all_courts_update": True,})
    return response



@user_passes_test(is_admin)
def add_upcoming_match_to_court(request, uuid, court_id, upcoming_match_id):

    session = get_object_or_404(Session, uuid=uuid)
    upcoming_match = get_object_or_404(UpcomingMatch, id=upcoming_match_id)
    court = get_object_or_404(
        Court, 
        id=court_id, 
        session=session
    )

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
    playersession__pause=False,
    playersession__session=session,
)
    
    p_waiting_ids = []
    p_waiting_ids = [p.id for p in players_waiting]

    upcoming_player_ids = [int(x) for x in upcoming_match.player_ids.split(",")]

    for p_id in upcoming_player_ids:
        if p_id not in p_waiting_ids:
            upcoming_match.delete()
            response = HttpResponse("Missing players to generate this game. Deleting Game.")
            response["HX-Trigger"] = json.dumps({
                f"upcoming_match_update": True})
            return response


    # Create new Match
    match = Match.objects.create(court=court)

    # Create two teams
    team1 = MatchTeam.objects.create(match=match, team_number=1)
    team2 = MatchTeam.objects.create(match=match, team_number=2)

    def create_player(player_id, team):
        player = Player.objects.get(id=player_id)
        MatchParticipant.objects.create(
            match_team=team,
            player=player
        )
    # Assign 2 players to each team
    create_player(upcoming_player_ids[0], team1)
    create_player(upcoming_player_ids[1], team1)
    create_player(upcoming_player_ids[2], team2)
    create_player(upcoming_player_ids[3], team2)


    messages.success(
        request, 
        f"New match started on Court {court.number}!"
    )

    UpcomingMatch.objects.filter(session__uuid=uuid).delete()

    response = HttpResponse("ok")
    response["HX-Trigger"] = json.dumps({
        "players_update": True,
        "upcoming_match_update": True,
        f"all_courts_update": True,
    })
    return response


@user_passes_test(is_admin)
def delete_upcoming_match(request, uuid, upcoming_match_id):

    get_object_or_404(UpcomingMatch, id=upcoming_match_id).delete()
    response = HttpResponse("ok")
    response["HX-Trigger"] = json.dumps({
        f"upcoming_match_update": True,
       "all_courts_update": True,})
    return response


@user_passes_test(is_admin)
def delete_upcoming_matches(request, uuid):

    UpcomingMatch.objects.filter(session__uuid=uuid).delete()
    response = HttpResponse("ok")
    response["HX-Trigger"] = json.dumps({
        f"upcoming_match_update": True,
         "all_courts_update": True,})
    return response
