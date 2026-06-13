
from ..models import Session, Match, Court, UpcomingMatch
from ..services.permissions import is_admin
from ..services.renders import render_courts, render_single_court, render_upcoming_match
from ..services.match_state import is_cancelled_game

from django.shortcuts import render, get_object_or_404
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
        render_courts(request, session)
        )

def single_court(request, uuid, court_id):
    session = get_object_or_404(Session, uuid=uuid)
    court = get_object_or_404(Court, id=court_id, session=session)
    
    context = render_single_court(request, session, court)
    return render(request, "match/partials/single_court.html", context)


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

        cancelled_game = is_cancelled_game(teams[0].score, teams[1].score)

        str_1 = f"{', '.join(p.player.name_coloured() for p in teams[0].participants.all())} {teams[0].score}"
        str_2 = f"{teams[1].score} {', '.join(p.player.name_coloured() for p in teams[1].participants.all())}"

        if len(teams) == 2:

            if not cancelled_game:
                line = (
                    f"{format_team(str_1, teams[0].is_winner)} - {format_team(str_2, teams[1].is_winner)}"
                )
            else:
                line = f"<s>{str_1} - {str_2}</s>"

            history.append({
                "court": match.court.number,
                "line": mark_safe(line),
            })

    return render(request, "match/partials/session_history.html", {
        "session": session,
        "history": history,
    })


def upcoming_match(request, uuid):
    session = get_object_or_404(Session, uuid=uuid)

    upcoming_match = UpcomingMatch.objects.filter(
        session=session
    ).order_by("-value").first()


    return render(request, "match/partials/upcoming_match.html", render_upcoming_match(request, session, upcoming_match))
