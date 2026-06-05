
from ..models import Session,  Player
from ..services.session_membership import add_player, remove_player

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test


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