from ..models import PlayerSession, Match
from .openskill import evaluate_win_differential, set_model

from collections import defaultdict
from itertools import combinations


from itertools import combinations
from collections import defaultdict


def eval_pair_games_played(players):
    """
    Evaluates repeat ratio for a single pair (used for blacklisting).
    Expects: players = [player1_dict, player2_dict]
    Returns: bool (keep)
    """
    if len(players) != 2:
        return False

    p1, p2 = players
    p1_id, p2_id = p1["id"], p2["id"]

    games_together = (p1.get("played_with", {}).get(p2_id, 0) +
                      p1.get("played_against", {}).get(p2_id, 0))

    if games_together == 0:
        return True

    p1_total = (sum(p1.get("played_with", {}).values()) +
                sum(p1.get("played_against", {}).values()))

    p2_total = (sum(p2.get("played_with", {}).values()) +
                sum(p2.get("played_against", {}).values()))

    if p1_total == 0 or p2_total == 0:
        return True

    avg_total_games = (p1_total + p2_total) / 2.0
    ratio = games_together / avg_total_games

    return ratio <= 0.32


def eval_match_played_against(teams):
    """Evaluates opponent freshness. Expects teams = (team1, team2)"""
    if not teams or len(teams) != 2:
        return False, 1.0

    team1, team2 = teams
    all_players = list(team1) + list(team2)

    if len(all_players) < 2:
        return False, 1.0

    total_ratio = 0.0
    active_players = 0

    for p in all_players:
        p_id = p["id"]
        played_against = p.get("played_against", {})
        total_games = (sum(p.get("played_with", {}).values()) +
                       sum(played_against.values()))

        if total_games == 0:
            continue

        repeat_games = 0
        opponent_count = 0

        opponents = team2 if p in team1 else team1
        for other in opponents:
            games_vs = played_against.get(other["id"], 0)
            if games_vs > 0:
                repeat_games += games_vs
                opponent_count += 1

        if opponent_count > 0:
            player_ratio = repeat_games / (total_games * opponent_count)
            total_ratio += player_ratio
            active_players += 1

    if active_players == 0:
        return False, 1.0

    avg_ratio = total_ratio / active_players
    unfairness = min(1.0, avg_ratio / 0.3)
    score = 1 - 2 * unfairness

    is_good = avg_ratio <= 0.32
    return is_good, score


def eval_match_played_with(teams):
    """Evaluates teammate freshness. Expects teams = (team1, team2)"""
    if not teams or len(teams) != 2:
        return False, 1.0

    team1, team2 = teams
    all_players = list(team1) + list(team2)

    total_ratio = 0.0
    active_players = 0

    for p in all_players:
        p_id = p["id"]
        played_with = p.get("played_with", {})
        total_games = (sum(played_with.values()) +
                       sum(p.get("played_against", {}).values()))

        if total_games == 0:
            continue

        repeat_games = 0
        teammate_count = 0

        teammates = team1 if p in team1 else team2
        for other in teammates:
            if other["id"] == p_id:
                continue
            games_with = played_with.get(other["id"], 0)
            if games_with > 0:
                repeat_games += games_with
                teammate_count += 1

        if teammate_count > 0:
            player_ratio = repeat_games / (total_games * teammate_count)
            total_ratio += player_ratio
            active_players += 1

    if active_players == 0:
        return True, 1.0

    avg_ratio = total_ratio / active_players
    unfairness = min(1.0, avg_ratio / 0.3)
    score = 1 - 2 * unfairness

    is_good = avg_ratio <= 0.32
    return is_good, score


def eval_match_fairness(teams):
    """Evaluates skill fairness. Expects teams = (team1, team2)"""
    if not teams or len(teams) != 2:
        return False, 1.0

    raw_diff = evaluate_win_differential(teams)

    unfairness = raw_diff ** 1.65
    fairness_score = 1 - 2 * unfairness
    fairness_score = max(min(fairness_score, 1.0), -1.0)

    is_fair = fairness_score >= 0.45
    return is_fair, fairness_score


# ====================== CONDITION REGISTRATION ======================

match_condition_funcs = {
    "played_against": {"func": eval_match_played_against, "weight": 3},
    "played_with":    {"func": eval_match_played_with,    "weight": 5},
    "fairness":       {"func": eval_match_fairness,       "weight": 10},
}

pair_condition_funcs = {
    "games_played": eval_pair_games_played,
}


# ====================== DATA PREPARATION ======================

def _calculate_played_with(session):
    """Calculate historical played_with and played_against counts."""
    matches = (
        Match.objects
        .filter(court__session=session)
        .prefetch_related("teams__participants")
    )

    played_with = defaultdict(lambda: defaultdict(int))
    played_against = defaultdict(lambda: defaultdict(int))

    for match in matches:
        teams = list(match.teams.all())
        if len(teams) != 2:
            continue

        t1 = teams[0]
        t2 = teams[1]

        team1 = [p.player_id for p in t1.participants.all()]
        team2 = [p.player_id for p in t2.participants.all()]

        # Same team (played_with)
        for team in (team1, team2):
            for i in range(len(team)):
                for j in range(i + 1, len(team)):
                    a, b = team[i], team[j]
                    played_with[a][b] += 1
                    played_with[b][a] += 1

        # Opposing teams (played_against)
        for a in team1:
            for b in team2:
                played_against[a][b] += 1
                played_against[b][a] += 1

    return played_with, played_against


def generate_config(players_waiting, session):
    """Generate player config with skill + history data."""
    played_with, played_against = _calculate_played_with(session)

    result = {}

    for p in players_waiting:
        result[p.id] = {
            "id": p.id,
            "name": p.name,
            "mu": p.mu,
            "sigma": p.sigma,
            "played_with": dict(played_with[p.id]),
            "played_against": dict(played_against[p.id])
        }

    return result

# ====================== MATCHMAKING HELPERS ======================

def contains_blacklisted_pair(team, blacklisted_pairs):
    """Check if any two players in the team are blacklisted (using IDs)."""
    if len(team) < 2:
        return False
    
    for p1, p2 in combinations(team, 2):
        pair = frozenset([p1["id"], p2["id"]])
        if pair in blacklisted_pairs:
            return True
    return False


def _splits(four, blacklisted_pairs):
    """Generate valid team splits (no blacklisted pairs within a team)."""
    a, b, c, d = four
    raw_splits = [
        ((a, b), (c, d)),
        ((a, c), (b, d)),
        ((a, d), (b, c)),
    ]

    for team1, team2 in raw_splits:
        if (not contains_blacklisted_pair(team1, blacklisted_pairs) and
            not contains_blacklisted_pair(team2, blacklisted_pairs)):
            yield team1, team2


def _get_blacklisted_pairs(players):
    """Pre-compute pairs that should NEVER be on the same team (using IDs)."""
    blacklisted = set()

    for p1, p2 in combinations(players, 2):
        keep = True
        for func in pair_condition_funcs.values():
            if not keep:
                break
            keep = func([p1, p2])

        if not keep:
            blacklisted.add(frozenset([p1["id"], p2["id"]]))

    return blacklisted


def matchmaking(players_waiting, session):
    set_model()
    players_dict = generate_config(players_waiting, session)
    players = list(players_dict.values())

    # 1. Pre-compute blacklisted pairs
    blacklisted_pairs = _get_blacklisted_pairs(players)

    potential_matches = []

    for four in combinations(players, 4):
        for team1, team2 in _splits(four, blacklisted_pairs):
            overall_score = 0.0
            keep = True

            for cond in match_condition_funcs.values():
                if not keep:
                    break
                keep, score = cond["func"]((team1, team2))
                overall_score += cond["weight"] * score

            if keep:
                potential_matches.append({
                    "teams": [team1, team2],
                    "score": overall_score
                })

    sorted_matches = sorted(potential_matches, key=lambda x: x["score"], reverse=True)
    return sorted_matches
