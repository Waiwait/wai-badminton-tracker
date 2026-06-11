
from ..models import Session, Player, Match, Court, MatchTeam, MatchParticipant
from ..services.permissions import is_admin
from ..services.session_membership import add_player, remove_player
from ..services.renders import render_matches, render_players
from ..services.openskill import score_match
from ..services.matchmaking import matchmaking

from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db import models


@user_passes_test(is_admin)
def add_player_to_session(request, uuid):
    session = get_object_or_404(Session, uuid=uuid)
    player = get_object_or_404(Player, id=request.POST["player_id"])

    add_player(session, player)

    return render(request, "match/partials/admin_players.html", render_players(session))


@user_passes_test(is_admin)
def remove_player_from_session(request, uuid, player_id):
    session = get_object_or_404(Session, uuid=uuid)
    player = get_object_or_404(Player, id=player_id)

    remove_player(session, player)

    return render(request, "match/partials/admin_players.html", render_players(session))


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

    # Determine winner
    if team1_score > team2_score:
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

    try:
        score_match(match)
    except Exception as e:
        print(e)


    messages.success(
        request, 
        f"Match on Court {match.court.number} finished! Score: {team1_score} - {team2_score}"
    )
    
    return render(request, "match/session_dashboard.html", {
        "session": session,
        "show_admin_panel": is_admin(request.user),
    })


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

    players_waiting = session_players.exclude(id__in=in_match_players)

    # Need at least 4 players
    if len(players_waiting) < 4:
        messages.error(request, "Not enough players waiting (need at least 4)")
        return render(request, "match/session_dashboard.html", {
        "session": session,
        "show_admin_panel": is_admin(request.user),
    })
    
    matches_ranked = matchmaking(players_waiting=players_waiting, session=session)

    for matches in matches_ranked[:5]:
        str_print = "[INFO] "
        for teams in matches["teams"]:
            for player in teams:
               str_print += f"{player['name']},"
        str_print += f": {matches["score"]}"
        print(str_print)
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

    return render(request, "match/session_dashboard.html", {
        "session": session,
        "show_admin_panel": is_admin(request.user),
    })


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
            messages.error(request, "Maximum of 4 courts allowed")

    return render(request, "match/partials/court_board.html", render_matches(request, session))

@user_passes_test(is_admin)
def release_court(request, uuid, court_id):
    session = get_object_or_404(Session, uuid=uuid)
    court = get_object_or_404(Court, id=court_id, session=session)

    # check for unfinished match
    has_active_match = court.matches.filter(finished=False).exists()

    if has_active_match:
        # don't allow deactivation
        return render(request, "match/session_dashboard.html", {
            "session": session,
            "error": "Cannot deactivate court: active match in progress",
            "show_admin_panel": is_admin(request.user),
        })

    court.active = False
    court.save()

    return render(request, "match/partials/court_board.html", render_matches(request, session))