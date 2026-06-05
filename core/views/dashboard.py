
from ..models import Session, PlayerSession, Player

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import user_passes_test


def session_detail(request, uuid):
    session = get_object_or_404(Session, uuid=uuid)

    matches = session.matches.all()
    players = PlayerSession.objects.filter(session=session)

    return render(request, "match/session_dashboard.html", {
        "session": session,
        "matches": matches,
        "players": players,
    })



def is_admin(user):
    return user.is_staff

@user_passes_test(is_admin)
def session_control_panel(request, uuid):
    session = get_object_or_404(Session, uuid=uuid)

    query = request.GET.get("q", "")

    already_in_session = PlayerSession.objects.filter(
        session=session
    ).values_list("player_id", flat=True)

    available_players = Player.objects.filter(
        name__icontains=query
    ).exclude(
        id__in=already_in_session
    )

    session_players = Player.objects.filter(
        id__in=already_in_session
    )

    return render(request, "match/session_control.html", {
        "session": session,
        "available_players": available_players,
        "session_players": session_players,
        "query": query
    })