from ..models import Player

from itertools import combinations
from openskill.models import PlackettLuce


def set_model():
    global model
    model = PlackettLuce()


def _match_weight(score_a, score_b):
    diff = abs(score_a - score_b)
    if diff <= 4:
        return 1
    elif diff <= 9:
        return 2
    else:
        return 3


def _play_match_with_weights(team_a, team_b, score_a, score_b):
    for _ in range(_match_weight(score_a, score_b)):
        # scoring doesn't matter here it's used for evaluating winner
        # which is why we need weighting
        team_a, team_b = model.rate([team_a, team_b], scores=[score_a, score_b])
    
    return team_a, team_b


def evaluate_win_differential(teams):

    team_a = [
        model.rating(mu=float(p["mu"]), sigma=float(p["sigma"]))
        for p in teams[0]
    ]

    team_b = [
        model.rating(mu=float(p["mu"]), sigma=float(p["sigma"]))
        for p in teams[1]
    ]
    predictions = model.predict_win([team_a, team_b])
    fairness = abs(predictions[0] - predictions[1])

    return fairness


def score_match(match):
    set_model()

    team1 = match.teams.get(team_number=1)
    team2 = match.teams.get(team_number=2)

    score1 = team1.score
    score2 = team2.score

    players_a = Player.objects.filter(matchparticipant__match_team=team1)
    players_b = Player.objects.filter(matchparticipant__match_team=team2)

    # Convert DB players → OpenSkill ratings
    team_a = [
        model.rating(mu=float(p.mu), sigma=float(p.sigma))
        for p in players_a
    ]

    team_b = [
        model.rating(mu=float(p.mu), sigma=float(p.sigma))
        for p in players_b
    ]

    # Run rating update
    team_a_updated, team_b_updated = _play_match_with_weights(
        team_a,
        team_b,
        score1,
        score2,
    )

    # Map results back to DB players
    for db_player, updated_rating in zip(players_a, team_a_updated):
        Player.objects.filter(id=db_player.id).update(
            mu=updated_rating.mu,
            sigma=updated_rating.sigma,
        )

    for db_player, updated_rating in zip(players_b, team_b_updated):
        Player.objects.filter(id=db_player.id).update(
            mu=updated_rating.mu,
            sigma=updated_rating.sigma,
        )


