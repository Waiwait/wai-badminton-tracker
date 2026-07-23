from ..models import PlayerSession, Match, Pair, GenderPair, MatchmakingConfig
from .openskill import evaluate_win_differential, set_model

from collections import defaultdict
from itertools import combinations


from itertools import combinations
from collections import defaultdict

# import time


def eval_pair_games_played(players):
    """
    Evaluates repeat ratio for a single pair (used for blacklisting).
    Expects: players = [player1_dict, player2_dict]
    Returns: bool (keep)
    """

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

    return ratio <= 0.4


def eval_pair_pairings(players):

    if players[0]["partner_id"] is None and players[1]["partner_id"] is None: return True
    if players[0]["id"] == players[1]["partner_id"] and players[1]["id"] == players[0]["partner_id"]: return True

    return False


def eval_gender_pair_requirement(players):
    """
    Checks whether players satisfy gender partner requirements.
    players = [player1, player2]
    """

    p1, p2 = players

    if p1["required_gender"] is not None:
        if p2["gender"] != p1["required_gender"]:
            return False

    if p2["required_gender"] is not None:
        if p1["gender"] != p2["required_gender"]:
            return False

    return True


def eval_match_played_against(teams):
    """Evaluates opponent freshness. Returns score in [-1, 1]."""
    if not teams or len(teams) != 2:
        return 1.0

    team1, team2 = teams
    all_players = list(team1) + list(team2)

    if len(all_players) < 2:
        return 1.0

    total_ratio = 0.0
    active_players = 0

    for p in all_players:
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
        return 1.0

    avg_ratio = total_ratio / active_players
    unfairness = min(1.0, avg_ratio / 0.3)
    score = 1 - 2 * unfairness

    return max(-1.0, min(1.0, score))


def eval_match_played_with(teams):
    """Evaluates teammate freshness. Returns score in [-1, 1]."""
    if not teams or len(teams) != 2:
        return 1.0

    team1, team2 = teams
    all_players = list(team1) + list(team2)

    total_ratio = 0.0
    active_players = 0

    for p in all_players:
        p_id = p["id"]
        played_with = p.get("played_with", {})
        total_games = (
            sum(played_with.values()) +
            sum(p.get("played_against", {}).values())
        )

        if total_games == 0:
            continue

        teammates = team1 if p in team1 else team2

        repeat_games = 0
        teammate_count = 0

        for other in teammates:
            if other["id"] == p_id:
                continue

            # Ignore mandatory pairings completely.
            if (
                p.get("partner_id") == other["id"] and
                other.get("partner_id") == p_id
            ):
                continue

            games_with = played_with.get(other["id"], 0)
            repeat_games += games_with
            teammate_count += 1

        # Team consisted only of a mandatory pair.
        if teammate_count == 0:
            continue

        player_ratio = repeat_games / (total_games * teammate_count)

        # Hard fail for excessive repeat teammates.
        if player_ratio >= 0.3:
            return -1.0

        total_ratio += player_ratio
        active_players += 1

    if active_players == 0:
        return 0.0  # Match only contained mandatory pairings.

    avg_ratio = total_ratio / active_players
    unfairness = min(1.0, avg_ratio / 0.3)
    score = 1 - 2 * unfairness

    return max(-1.0, min(1.0, score))


def eval_games_played(teams):
    """Evaluates playtime fairness using pre-normalized scores."""
    if not teams or len(teams) != 2:
        return 1.0

    gps_list = [
        player.get("games_played_score")
        for team in teams
        for player in team
    ]

    if not gps_list:
        return 1.0

    avg_score = sum(gps_list) / len(gps_list)
    return max(-1.0, min(1.0, avg_score))


def eval_gender_balance(teams):
    """Evaluates gender balance. Returns score in [-1, 1]."""
    if not teams or len(teams) != 2:
        return 0.0

    team1, team2 = teams

    def get_composition(team):
        males = sum(1 for p in team if p.get("gender") == "M")
        if males == 2:
            return "MM"
        elif males == 0:
            return "FF"
        else:
            return "MF"

    t1 = get_composition(team1)
    t2 = get_composition(team2)

    if t1 == t2:
        return 1

    elif (t1 == "MM" and t2 == "FF") or (t1 == "FF" and t2 == "MM"):
        return -1                                     # Worst case

    else:
        return 0.2


def eval_match_fairness(teams):
    """Evaluates skill fairness. Returns score in [-1, 1]."""
    raw_diff = evaluate_win_differential(teams)

    unfairness = raw_diff ** 1.65
    score = 1 - 2 * unfairness
    return max(-1.0, min(1.0, score))


def eval_skill_difference(teams):
    """
    Evaluates intra-team skill balance using relative gap.
    Returns score in [-1, 1].
    """
    if not teams or len(teams) != 2:
        return 1.0

    # Get global range from first player
    sample = teams[0][0] if teams[0] else teams[1][0]
    max_str = sample.get("max_strength", 0)
    min_str = sample.get("min_strength", 0)
    
    global_range = max_str - min_str
    if global_range <= 0:
        return 1.0


    def team_skill_gap(team):
        if len(team) < 2:
            return 0.0
        # Women rated 4 points higher since same strength women/men means women is more "skilled"
        strengths = [
            float(p.get("mu", 0)) + (4 if p.get("gender") == "F" else 0)
            for p in team
        ]
        return max(strengths) - min(strengths)

    max_gap = max(team_skill_gap(teams[0]), team_skill_gap(teams[1]))
    rel_gap = max_gap / global_range   # now safely float

    # Hardcoded thresholds (you can tweak these)
    if rel_gap <= 0.20:           # Top 20% of range
        score = 1.0
    elif rel_gap <= 0.35:
        score = 1.0 - (rel_gap - 0.20) / 0.15 * 1.6
    elif rel_gap <= 0.50:
        score = 1.0 - (rel_gap - 0.20) / 0.30 * 2.8
    else:
        score = -0.6 - (rel_gap - 0.50) * 3.0   # steep penalty beyond 50%

    return max(-1.0, min(1.0, round(score, 3)))


# ====================== CONDITION REGISTRATION ======================


def get_match_condition_funcs():
    """Return condition functions with live weights from database"""
    config = MatchmakingConfig.get_config()
    
    return {
        "games_played": {
            "func": eval_games_played,
            "weight": config.games_played_weight
        },
        
        "played_with": {
            "func": eval_match_played_with,
            "weight": config.played_with_weight
        },
        "played_against": {
            "func": eval_match_played_against,
            "weight": config.played_against_weight
        },
        "gender": {
            "func": eval_gender_balance,
            "weight": config.gender_weight
        },
        "skill_difference": {
            "func": eval_skill_difference,
            "weight": config.skill_difference_weight
        },
        "fairness": {
            "func": eval_match_fairness,
            "weight": config.fairness_weight
        },
    }


pair_condition_funcs = {
    "games_played": eval_pair_games_played,
    "pairing": eval_pair_pairings,
    "gender_pairing": eval_gender_pair_requirement,
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


def _calculate_normalised_playtime(players_waiting, player_sessions):
    ratios = {}
    for p in players_waiting:
        ps = player_sessions.get(p.id)
        gp = ps.games_played if ps else 0
        gs = ps.games_skipped if ps else 0
        ratio = gp / (gp + gs + 1)                    # base play ratio
        ratios[p.id] = ratio

    if ratios:
        min_ratio = min(ratios.values())
        max_ratio = max(ratios.values())
        range_ratio = max(1e-5, max_ratio - min_ratio)   # avoid div by zero

        # Normalized fairness score: -1.0 (played too much) → +1.0 (needs to play)
        for pid, ratio in ratios.items():
            normalized = (ratio - min_ratio) / range_ratio          # 0 to 1
            fairness_score = 1.0 - 2.0 * normalized                 # invert → -1 to +1
            ratios[pid] = round(fairness_score, 3)                  # store back
    else:
        # No players
        return 
    
    return ratios


def generate_config(players_waiting, session):
    """Generate player config with skill + history data."""
    played_with, played_against = _calculate_played_with(session)


    # Pre-fetch PlayerSession records for all waiting players in one query
    player_sessions = {
        ps.player_id: ps 
        for ps in PlayerSession.objects.filter(
            session=session,
            player_id__in=[p.id for p in players_waiting]
        )
    }

    result = {}

    partners = {}

    pairs = Pair.objects.filter(session=session).values_list(
    'player1_s__player_id',
    'player2_s__player_id',
)
    for p1_id, p2_id in pairs:
        partners[p1_id] = p2_id
        partners[p2_id] = p1_id

    # Gender pairs
    gender_requirements = {}
    gender_pairs = GenderPair.objects.filter(session=session).values_list(
        "player1_s__player_id",
        "gender",
    )

    for player_id, gender in gender_pairs:
        gender_requirements[player_id] = gender

    games_played_score = _calculate_normalised_playtime(players_waiting, player_sessions)

    all_mus = [p.mu for p in players_waiting]
    global_min_mu = min(all_mus) if all_mus else 0
    global_max_mu = max(all_mus) if all_mus else 0


    for p in players_waiting:

        result[p.id] = {
            "id": p.id,
            "name": p.name,
            "gender": p.gender,
            "mu": float(p.mu),
            "sigma": float(p.sigma),
            "min_strength": float(global_min_mu),
            "max_strength": float(global_max_mu),
            "sigma": p.sigma,
            "games_played_score": games_played_score.get(p.id, 0.0),
            "played_with": dict(played_with[p.id]),
            "played_against": dict(played_against[p.id]),
            "partner_id": partners.get(p.id, None),
            "required_gender": gender_requirements.get(p.id, None),
        }

    return result

# ====================== MATCHMAKING HELPERS ======================

def contains_blacklisted_pair(team, blacklisted_pairs):
    """Check if any two players in the team are blacklisted (using IDs)."""
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


def matchmaking(players_waiting, session, top_n=5, max_players_before_sampling=16):
    set_model()
    players_dict = generate_config(players_waiting, session)
    players = list(players_dict.values())

    # To keep this bounded, only take top x players who have played the least matches
    if len(players) > max_players_before_sampling:
        players = sorted(
            players,
            key=lambda p: p["games_played_score"],
            reverse=True,  
        )[:max_players_before_sampling]


    blacklisted_pairs = _get_blacklisted_pairs(players)

    potential_matches = []
    best_scores = []

    match_cond_funcs = get_match_condition_funcs()

    # start = time.perf_counter()
    # itx = 0

    for four in combinations(players, 4):
        for team1, team2 in _splits(four, blacklisted_pairs):
            overall_score = 0.0

            for cond in match_cond_funcs.values():
                score = cond["func"]((team1, team2))
                overall_score += cond["weight"] * score

            potential_matches.append({
                "teams": [team1, team2],
                "score": overall_score
            })

    # elapsed = time.perf_counter() - start
    # print(f"{elapsed}s, {itx}")

    # Final sort (only the survivors)
    # after the loops
    sorted_matches = sorted(
        potential_matches,
        key=lambda x: x["score"],
        reverse=True
    )

    # guarantees uniqueness
    used_scores = set()

    for match in sorted_matches:
        score = round(match["score"], 2)

        while score in used_scores:
            score = round(score - 0.01, 2)

        match["score"] = score
        used_scores.add(score)

    return sorted_matches[:top_n]
