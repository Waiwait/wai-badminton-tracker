
from ..models import Session,  Player
from ..services.session_membership import add_player, remove_player

from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import user_passes_test


def court_board(request, uuid):
    session = get_object_or_404(Session, uuid=uuid)
    courts = session.courts.all().order_by("number")

    court_data = []

    for court in courts:
        match = court.matches.filter(finished=False).first()
        court_data.append({
            "court": court,
            "match": match
        })

    return render(request, "match/partials/court_board.html", {
        "session": session,
        "court_data": court_data,
    })


def is_admin(user):
    return user.is_staff


@user_passes_test(is_admin)
def add_player_to_session(request, uuid):
    session = get_object_or_404(Session, uuid=uuid)
    player = get_object_or_404(Player, id=request.POST["player_id"])

    add_player(session, player)

    return redirect("session_control", uuid=uuid)


@user_passes_test(is_admin)
def remove_player_from_session(request, uuid, player_id):
    session = get_object_or_404(Session, uuid=uuid)
    player = get_object_or_404(Player, id=player_id)

    remove_player(session, player)

    return redirect("session_control", uuid=uuid)


