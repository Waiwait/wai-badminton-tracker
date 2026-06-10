from .permissions import is_admin


def render_matches(request, session):
    courts = session.courts.all().order_by("number")

    court_data = []

    for court in courts:
        match = court.matches.filter(finished=False).first()

        team1 = []
        team2 = []

        if match: 
            for team in match.teams.all():
                if team.team_number == 1:
                    team1 = [p.player for p in team.participants.all()]
                else:
                    team2 = [p.player for p in team.participants.all()]

        court_data.append({
            "court": court,
            "match": match if match else None,
            "team1": team1,
            "team2": team2,
        })

    return {
        "session": session,
        "court_data": court_data,
        "show_admin_panel": is_admin(request.user),
    }
