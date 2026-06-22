from ..models import Player

from django.db import transaction
from bs4 import BeautifulSoup


EBADDERS_RANK_TO_MU = {
    "A+": 40.0,
    "A": 37.5,
    "A-": 35.0,
    "B+": 32.5,
    "B": 30.0,
    "B-": 27.5,
    "C+": 25.0,
    "C": 22.5,
    "C-": 20.0,
    "D+": 17.5,
    "D": 15.0,
    "D-": 12.5,
    "E": 10.0,
}

EBADDERS_FEMALE_ADJUSTMENT = 3.75


def load_user_data_ebadders(html: str):
    """Import Players from ebadders player HTML page."""

    soup = BeautifulSoup(html, "html.parser")

    players_dict = {}

    for row in soup.select("tr.filterable"):
        cols = row.find_all("td")

        if len(cols) < 6:
            continue

        # Rank column
        rank = cols[1].get_text(strip=True)

        # Name span
        name_span = cols[2].find("span")
        if not name_span:
            continue

        name = name_span.get_text(" ", strip=True)

        # Remove inactive players
        if "inactive" in name.lower():
            continue

        # Detect gender from class
        classes = name_span.get("class", [])
        gender = "F" if "female" in classes else "M"

        # Rank -> mu
        mu = EBADDERS_RANK_TO_MU.get(rank, 25.0)

        # female adjustment
        if gender == "F":
            mu -= EBADDERS_FEMALE_ADJUSTMENT

        players_dict[name] = {
            "name": name,
            "gender": gender,
            "mu": mu,
            "sigma": 4.0,
        }

    return players_dict




def load_user_data_superbadders(restore_string: str):
    """Parse SuperBadders restore string."""

    players_dict = {}
    parts = restore_string.split('&')

    for part in parts:
        if not part.startswith('p') or '=' not in part:
            continue

        key, value = part.split('=', 1)
        if not key.startswith('p'):
            continue

        fields = value.split(':')
        if len(fields) < 3:
            continue

        name = fields[0].replace('%20', ' ').strip()
        gender = fields[1]

        try:
            mu = float(fields[10])
        except (ValueError, IndexError):
            mu = 0

        player_id = key  # p0, p1, etc. — we can ignore this or use as temp key

        players_dict[name] = {          # Use name as key to avoid duplicates
            "name": name,
            "gender": gender,
            "mu": mu,
            "sigma": 3.0,
        }

    return players_dict



def create_players(players_data):
            
    with transaction.atomic():

        Player.objects.all().delete()
        created = 0

        for name, pdata in players_data.items():
                
            Player.objects.create(
                name=name,
                gender=pdata['gender'],
                mu=pdata['mu'],
                sigma=pdata['sigma'],
            )
            created += 1

    return created
