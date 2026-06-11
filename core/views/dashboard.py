
from ..models import Session, Match
from ..services.permissions import is_admin
from ..services.renders import render_matches

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.utils.safestring import mark_safe


def session_detail(request, uuid):
    session = get_object_or_404(Session, uuid=uuid)
    return render(request, "match/session_dashboard.html", {
        "session": session,
        "show_admin_panel": is_admin(request.user),
    })


def court_board(request, uuid):
    session = get_object_or_404(Session, uuid=uuid)
    return render(
        request,
        "match/partials/court_board.html",
        render_matches(request, session)
        )


def session_history(request, uuid):
    session = get_object_or_404(Session, uuid=uuid)

    matches = (
        Match.objects
        .filter(court__session=session, finished=True)
        .prefetch_related("teams__participants__player")
        .select_related("court")
        .order_by("-id")
    )

    history = []

    def format_team(score_string, is_winner):
        if is_winner:
            return f"<strong>{score_string}</strong>"
        return f"{score_string}"


    for match in matches:
        teams = list(match.teams.all())

        str_1 = f"{', '.join(p.player.name for p in teams[0].participants.all())} {teams[0].score}"
        str_2 = f"{teams[1].score} {', '.join(p.player.name for p in teams[1].participants.all())}"

        if len(teams) == 2:
            line = (
                f"{format_team(str_1, teams[0].is_winner)} - {format_team(str_2, teams[1].is_winner)}"
            )

            history.append({
                "court": match.court.number,
                "line": mark_safe(line),
            })

    return render(request, "match/partials/session_history.html", {
        "session": session,
        "history": history,
    })


@user_passes_test(is_admin)
def admin_dashboard(request, uuid):
    session = get_object_or_404(Session, uuid=uuid)
    return render(request, "match/partials/admin_dashboard.html", {
        "session": session,
    })
