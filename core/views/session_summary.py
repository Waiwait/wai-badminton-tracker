
from ..models import Session, Match, ClubConfig
from collections import defaultdict

from django.shortcuts import render, get_object_or_404
from django.utils.safestring import mark_safe




def session_summary(request, uuid):
    session = get_object_or_404(Session, uuid=uuid)

    # Stats keyed by Player
    stats = defaultdict(lambda: {"wins": 0, "losses": 0})

    # All finished matches in this session
    matches = Match.objects.filter(
        court__session=session,
        finished=True,
    ).prefetch_related("teams__participants__player")

    for match in matches:
        winner_team = match.teams.filter(is_winner=True).first()

        if winner_team is None:
            continue

        loser_team = match.teams.exclude(id=winner_team.id).first()

        for participant in winner_team.participants.all():
            stats[participant.player]["wins"] += 1

        if loser_team:
            for participant in loser_team.participants.all():
                stats[participant.player]["losses"] += 1

    players_in_session = []

    # Sort by games played (descending), then name
    sorted_players = sorted(
        stats.items(),
        key=lambda x: (
            -((x[1]["wins"] / (x[1]["wins"] + x[1]["losses"])) if (x[1]["wins"] + x[1]["losses"]) else 0),
            -(x[1]["wins"] + x[1]["losses"]),
            x[0].name,
        )
    )

    players_in_session = []

    for i, (player, s) in enumerate(sorted_players):
        wins = s["wins"]
        losses = s["losses"]
        games = wins + losses
        win_rate = wins / games * 100

        name = player.name_coloured()

        players_in_session.append({
            "name": mark_safe(name),
            "games": games,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "rank": i + 1,
        })

    return render(request, "summary/session_summary.html", {
        "session": session,
        "players_in_session": players_in_session,
        "club_name": ClubConfig.get("club_name", "WBT")
    })
