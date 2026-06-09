
from ..models import Session, Player
from ..services.permissions import is_admin
from ..services.session_membership import add_player, remove_player, render_players

from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import user_passes_test



def court_board(request, uuid):
    session = get_object_or_404(Session, uuid=uuid)
    courts = session.courts.all().order_by("number")

    court_data = []

    for court in courts:
        match = court.matches.filter(finished=False).first()

        if match:
            participants = match.participants.select_related("player")

            team1 = [p.player for p in participants if p.team == 1]
            team2 = [p.player for p in participants if p.team == 2]
        else:
            team1 = []
            team2 = []

        court_data.append({
            "court": court,
            "team1": team1,
            "team2": team2,
        })

    return render(request, "match/partials/court_board.html", {
        "session": session,
        "court_data": court_data,
    })



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


