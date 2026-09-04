from ..models import (
    Session, Player, Match, Court, MatchTeam,
    MatchParticipant, PlayerSession, UpcomingMatch,
    Pair, GenderPair, ClubConfig
)
from ..services.permissions import is_admin
from ..services.session_membership import add_player, remove_player
from ..services.openskill import score_match
from ..services.matchmaking import matchmaking
from ..services.match_state import is_cancelled_game
from ..services.sse import notify_session

import json
from decimal import Decimal, InvalidOperation

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import user_passes_test
from django.db import models, transaction
from django.db.models import F, Max, Q


def hx_response(message=None, triggers=None, status=200):
    response = HttpResponse("ok", status=status)

    payload = triggers or {}

    if message:
        payload["showToast"] = {
            "message": message
        }

    response["HX-Trigger"] = json.dumps(payload)

    return response



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

    return hx_response(
        triggers={
            "players_update": True,
            "waiting_update": True,
            "paused_update": True,
            "pairs_update": True,
            "switch_players_update": True,
        }
    )


@user_passes_test(is_admin)
def pause_player_in_session(request, uuid, player_id):
    session = get_object_or_404(Session, uuid=uuid)
    player = get_object_or_404(Player, id=player_id)

    PlayerSession.objects.filter(
        session=session,
        player=player
    ).update(pause=True)

    response = render(request, "match/partials/player_row.html", {
        "player": player,
        "state": "paused",
        "session": session,
    })
    response["HX-Trigger"] = json.dumps({
        "waiting_update": True,
        "paused_update": True,
        "pairs_update": True,
        "switch_players_update": True,
    })

    return response

@user_passes_test(is_admin)
def unpause_player_in_session(request, uuid, player_id):
    session = get_object_or_404(Session, uuid=uuid)
    player = get_object_or_404(Player, id=player_id)

    ps = PlayerSession.objects.get(session=session, player=player)
    ps.pause = False
    ps.save(update_fields=["pause"])

    response = render(request, "match/partials/player_row.html", {
        "player": player,
        "state": "waiting",
        "session": session,
    })

    response["HX-Trigger"] = json.dumps({
        "waiting_update": True,
        "paused_update": True,
        "pairs_update": True,
        "switch_players_update": True,
    })

    return response


@user_passes_test(is_admin)
def unpause_player_in_session(request, uuid, player_id):
    session = get_object_or_404(Session, uuid=uuid)
    player = get_object_or_404(Player, id=player_id)

    ps = PlayerSession.objects.get(
        session=session,
        player=player
    )

    ps.pause = False
    ps.save(update_fields=["pause"])

    response = render(request, "match/partials/player_row.html", {
        "player": player,
        "state": "waiting",
        "session": session,
    })

    response["HX-Trigger"] = json.dumps({
        "waiting_update": True,
        "paused_update": True,
        "pairs_update": True,
        "switch_players_update": True,
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

    team1_score = int(request.POST.get("team1_score", 0))
    team2_score = int(request.POST.get("team2_score", 0))

    team1 = match.teams.get(team_number=1)
    team2 = match.teams.get(team_number=2)

    team1.score = team1_score
    team2.score = team2_score

    cancelled_game = is_cancelled_game(
        team1_score,
        team2_score
    )

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

    toast_message = None

    if not cancelled_game:
        try:
            score_match(match)

        except Exception as e:
            toast_message = (
                f"Match on Court {match.court.number} finished! "
                f"Could not score match: {e}"
            )


    if not cancelled_game:

        played_players = set()

        for team in [team1, team2]:
            for participant in team.participants.all():
                played_players.add(
                    participant.player_id
                )

        player_sessions = PlayerSession.objects.filter(
            session=session,
            pause=False
        )

        updates = []

        for ps in player_sessions:

            if ps.player_id in played_players:
                ps.games_played = (
                    models.F("games_played") + 1
                )

            else:
                ps.games_skipped = (
                    models.F("games_skipped") + 1
                )

            updates.append(ps)

        if updates:
            PlayerSession.objects.bulk_update(
                updates,
                [
                    "games_played",
                    "games_skipped"
                ]
            )

    if toast_message:
        message = toast_message
    elif cancelled_game:
        message = f"Match on Court {match.court.number} finished! Treating game as cancelled as score is below threshold"
    else:
        message =  (
            f"Match on Court {match.court.number} finished! "
            f"Score: {team1_score} - {team2_score}"
        ),

    return hx_response(
        message=message,
        triggers={
            "players_update": True,
            f"court_{match.court.id}_update": True,
            "history_update": True,
            "switch_players_update": True,
        }
    )

@user_passes_test(is_admin)
def add_court(request, uuid):
    session = get_object_or_404(Session, uuid=uuid)

    court = session.courts.filter(
        active=False
    ).order_by("number").first()

    max_courts = int(ClubConfig.get("max_courts", "4"))
    if court:
        court.active = True
        court.save()

    else:
        last_number = (
            session.courts.aggregate(
                models.Max("number")
            )["number__max"] or 0
        )

        if last_number <= max_courts-1:
            court = Court.objects.create(
                session=session,
                number=last_number + 1,
                active=True
            )

        else:
            return hx_response(
                message=f"Maximum of {max_courts} courts allowed. Change this in club config"
            )

    return hx_response(
        triggers={
            "court_board_update": True,
        }
    )



@user_passes_test(is_admin)
def release_court(request, uuid, court_id):
    session = get_object_or_404(Session, uuid=uuid)

    court = get_object_or_404(
        Court,
        id=court_id,
        session=session
    )

    has_active_match = court.matches.filter(
        finished=False
    ).exists()

    if has_active_match:
        return hx_response(
            message="Cannot deactivate court: active match in progress"
        )

    court.active = False
    court.save()

    return hx_response(
        triggers={
            f"court_{court.id}_update": True
        }
    )



@user_passes_test(is_admin)
def generate_upcoming_match(request, uuid, queue_number):

    session = get_object_or_404(
        Session,
        uuid=uuid
    )

    session_players = Player.objects.filter(
        playersession__session=session
    ).distinct()

    in_match_players = Player.objects.filter(
        matchparticipant__match_team__match__court__session=session,
        matchparticipant__match_team__match__finished=False
    ).distinct()


    highest_values = UpcomingMatch.objects.filter(
        session=session
    ).values(
        'queue_number'
    ).annotate(
        highest_value=Max('value')
    )

    for item in highest_values:
        UpcomingMatch.objects.filter(
            session=session,
            queue_number=item['queue_number']
        ).exclude(
            value=item['highest_value']
        ).delete()


    upcoming_player_ids = []
    for match in UpcomingMatch.objects.filter(session=session):
        upcoming_player_ids.extend(match.player_ids.split(","))

    players_waiting = session_players.exclude(
        id__in=in_match_players
    ).filter(
        playersession__pause=False,
        playersession__session=session,
    )
    players_waiting = players_waiting.exclude(
            id__in=upcoming_player_ids
        )

    if players_waiting.count() < 4:
        return hx_response(
            message="Need 4+ waiting players to generate an upcoming game"
        )


    upcoming_matches = matchmaking(
        players_waiting=players_waiting,
        session=session
    )


    if len(upcoming_matches) == 0:
        return hx_response(
            message=(
                "No games can be generated with constraints, "
                "check pairs or allow more players to finish their games"
            )
        )


    for upcoming_match in upcoming_matches:

        p_ids = []

        for team in upcoming_match["teams"]:
            for player in team:
                p_ids.append(
                    str(player["id"])
                )

        UpcomingMatch.objects.create(
            value=upcoming_match["score"],
            session=session,
            player_ids=",".join(p_ids),
            queue_number=queue_number,
        )


    return hx_response(
        message="Matchmaking successful! Add upcoming match to a free court or regenerate",
        triggers={
            "players_update": True,
            "upcoming_match_update": True,
            "all_courts_update": True,
            "switch_players_update": True,
        }
    )



@user_passes_test(is_admin)
def add_upcoming_match_to_court(
    request,
    uuid,
    court_id,
    upcoming_match_id
):

    session = get_object_or_404(
        Session,
        uuid=uuid
    )

    upcoming_match = get_object_or_404(
        UpcomingMatch,
        id=upcoming_match_id
    )

    court = get_object_or_404(
        Court,
        id=court_id,
        session=session
    )


    session_players = Player.objects.filter(
        playersession__session=session
    ).distinct()


    in_match_players = Player.objects.filter(
        matchparticipant__match_team__match__court__session=session,
        matchparticipant__match_team__match__finished=False
    ).distinct()


    players_waiting = session_players.exclude(
        id__in=in_match_players
    ).filter(
        playersession__pause=False,
        playersession__session=session,
    )


    p_waiting_ids = [
        p.id for p in players_waiting
    ]


    upcoming_player_ids = [
        int(x)
        for x in upcoming_match.player_ids.split(",")
    ]


    for p_id in upcoming_player_ids:

        if p_id not in p_waiting_ids:

            upcoming_match.delete()

            return hx_response(
                message=(
                    "Missing players to generate this game. "
                    "Deleting game."
                ),
                triggers={
                    "upcoming_match_update": True
                }
            )


    match = Match.objects.create(
        court=court
    )


    team1 = MatchTeam.objects.create(
        match=match,
        team_number=1
    )

    team2 = MatchTeam.objects.create(
        match=match,
        team_number=2
    )


    def create_player(player_id, team):

        player = Player.objects.get(
            id=player_id
        )

        MatchParticipant.objects.create(
            match_team=team,
            player=player
        )


    create_player(upcoming_player_ids[0], team1)
    create_player(upcoming_player_ids[1], team1)
    create_player(upcoming_player_ids[2], team2)
    create_player(upcoming_player_ids[3], team2)


    UpcomingMatch.objects.filter(
        session__uuid=uuid,
        queue_number=0
    ).delete()

    UpcomingMatch.objects.filter(
        session__uuid=uuid,
        queue_number__gt=0
    ).update(
        queue_number=F('queue_number') - 1
    )
    

    return hx_response(
        message=f"New match started on Court {court.number}!",
        triggers={
            "players_update": True,
            "upcoming_match_update": True,
            "all_courts_update": True,
            
        }
    )


@user_passes_test(is_admin)
def delete_upcoming_match(request, uuid, upcoming_match_id):

    session = get_object_or_404(Session, uuid=uuid)
    upcoming_match = get_object_or_404(
        UpcomingMatch,
        id=upcoming_match_id
    )

    queue_number = upcoming_match.queue_number


    upcoming_match.delete()
    matches_remaining_in_queue = UpcomingMatch.objects.filter(
        session=session,
        queue_number=queue_number,
    ).count()

    if matches_remaining_in_queue == 0:
        return hx_response(
            message="Deleted the upcoming match. Allow more players to finish before generating for different games",
            triggers={
                "switch_players_update": True,
                "upcoming_match_update": True,
                "all_courts_update": True,
            }
        )


    return hx_response(
        message=f"Regenerated the upcoming match, {matches_remaining_in_queue} remaining",
        triggers={
            "players_update": True,
            "switch_players_update": True,
            f"upcoming_match_update_{queue_number}": True,
        }
    )


@user_passes_test(is_admin)
def delete_upcoming_matches(request, uuid, queue_number):

    with transaction.atomic():
        UpcomingMatch.objects.filter(
            session__uuid=uuid,
            queue_number=queue_number
        ).delete()

        UpcomingMatch.objects.filter(
            session__uuid=uuid,
            queue_number__gt=queue_number
        ).update(
            queue_number=F('queue_number') - 1
        )

    return hx_response(
        triggers={
            "players_update": True,
            "switch_players_update": True,
            "upcoming_match_update": True,
            "all_courts_update": True,
        }
    )
@user_passes_test(is_admin)
def add_pair(request, uuid):
    session = get_object_or_404(Session, uuid=uuid)

    p1_s_id = request.POST.get("p1_s_id")
    p2_s_id = request.POST.get("p2_s_id")


    if not PlayerSession.objects.filter(
        id=p1_s_id,
        session=session
    ).exists():

        return hx_response(
            message="Player 1 not found in session",
            status=400
        )


    used_player_ids = set()


    for pair in Pair.objects.filter(session=session):
        used_player_ids.add(pair.player1_s_id)
        used_player_ids.add(pair.player2_s_id)


    for gender_pair in GenderPair.objects.filter(session=session):
        used_player_ids.add(gender_pair.player1_s_id)


    if p1_s_id in used_player_ids:

        return hx_response(
            message=f"Player {p1_s_id} is already paired",
            status=400
        )


    if p2_s_id.startswith("gender_"):

        gender = p2_s_id.replace(
            "gender_",
            ""
        )

        GenderPair.objects.create(
            session=session,
            player1_s_id=p1_s_id,
            gender=gender,
        )


    else:

        if p1_s_id == p2_s_id:

            return hx_response(
                message="User cannot pair with himself",
                status=400
            )


        if p2_s_id in used_player_ids:

            return hx_response(
                message=f"Player {p2_s_id} is already paired",
                status=400
            )


        if not PlayerSession.objects.filter(
            id=p2_s_id,
            session=session
        ).exists():

            return hx_response(
                message="Player 2 not found in session",
                status=400
            )


        Pair.objects.create(
            session=session,
            player1_s_id=p1_s_id,
            player2_s_id=p2_s_id,
        )


    return hx_response(
        triggers={
            "pairs_update": True,
        }
    )



@user_passes_test(is_admin)
def delete_pair(request, uuid, pair_id):

    pair_model = (
        GenderPair
        if request.GET.get("gender_pair") == "true"
        else Pair
    )


    pair_model.objects.filter(
        id=pair_id,
        session__uuid=uuid,
    ).delete()


    return hx_response(
        triggers={
            "pairs_update": True,
        }
    )



@user_passes_test(is_admin)
def add_new_player(request, uuid):

    p_name = request.POST.get(
        "player_name"
    )


    if Player.objects.filter(
        name=p_name
    ).exists():

        return hx_response(
            message="Player name already exists",
            status=400
        )


    if not p_name:

        return hx_response(
            message="Missing name",
            status=400
        )


    p_gender = request.POST.get(
        "player_gender"
    )


    try:
        p_mu = Decimal(
            request.POST.get("player_strength")
        )

    except (
        TypeError,
        InvalidOperation
    ):

        return hx_response(
            message="Invalid strength",
            status=400
        )


    session = get_object_or_404(
        Session,
        uuid=uuid
    )


    player = Player.objects.create(
        name=p_name,
        gender=p_gender,
        mu=p_mu
    )


    PlayerSession.objects.create(
        session=session,
        player=player
    )


    return hx_response(
        triggers={
            "players_update": True,
            "pairs_update": True,
            "new_player_update": True,
            "switch_players_update": True,
        }
    )


@user_passes_test(is_admin)
def switch_players(request, uuid):


    UPDATE_TRIGGERS = {
        "players_update": True,
        "switch_players_update": True,
    }

    p1_id = request.POST.get("player1_id")
    p2_id = request.POST.get("player2_id")

    if not p1_id or not p2_id:
        return hx_response(message="Missing players", status=400)

    if p1_id == p2_id:
        return hx_response(message="Cannot switch same player", status=400)

    session = get_object_or_404(Session, uuid=uuid)

    player1 = get_object_or_404(Player, pk=p1_id)
    player2 = get_object_or_404(Player, pk=p2_id)

    # Player 2 cannot already be in an active match or upcoming match
    # ==
    if MatchParticipant.objects.filter(
        player=player2,
        match_team__match__court__session=session,
        match_team__match__finished=False,
    ).exists():
        return hx_response(
            message="Player 2 is already in an active match",
            status=400,
        )

    upcoming_matches_dict = UpcomingMatch.objects.filter(
            session=session
        ).values(
            'queue_number',
        ).annotate(
            highest_value=Max('value')
        )
    
    player_ids_upcoming_matches = []
    if upcoming_matches_dict.exists():
        for upcoming_match_dict in upcoming_matches_dict:
            upcoming_match = UpcomingMatch.objects.filter(
                session=session,
                queue_number=upcoming_match_dict['queue_number'],
                value=upcoming_match_dict['highest_value']
                ).first()
            player_ids_match = [int(x) for x in upcoming_match.player_ids.split(",")]
            if player2.id in player_ids_match:
                return hx_response(
                    message="Player 2 is in upcoming match",
                    status=400,
                )
            player_ids_upcoming_matches.append({
                "player_ids": player_ids_match,
                "upcoming_match": upcoming_match,
            })
    # ==

    # Find player1 in an active match
    mp1 = MatchParticipant.objects.filter(
        player=player1,
        match_team__match__court__session=session,
        match_team__match__finished=False,
    ).first()

    if mp1:
        with transaction.atomic():
            mp1.player = player2
            mp1.save()

        return hx_response(
            message="Player in active match switched!",
            triggers=UPDATE_TRIGGERS | { "all_courts_update": True }
            )

    if not upcoming_matches_dict.exists():
        return hx_response(
            message="Player 1 is not in an active or upcoming match",
            status=400,
        )

    for p_ids in player_ids_upcoming_matches:
        player_ids = p_ids["player_ids"]
        upcoming_match = p_ids["upcoming_match"]
        if player1.id in player_ids:
            player_ids[player_ids.index(player1.id)] = player2.id
            upcoming_match.player_ids = ",".join(map(str, player_ids))
            upcoming_match_queue_number = upcoming_match.queue_number

            with transaction.atomic():
                upcoming_match.save()

                for item in upcoming_matches_dict:
                    UpcomingMatch.objects.filter(
                        session=session,
                        queue_number=item['queue_number']
                    ).exclude(
                        value=item['highest_value']
                    ).delete()
                
    
            return hx_response(
                    message="Player in upcoming match switched!",
                    triggers=UPDATE_TRIGGERS | { f"upcoming_match_update_{upcoming_match_queue_number}": True }
                )

    return hx_response(
        message="Player 1 is not in any upcoming matches",
        status=400,
    )

    
