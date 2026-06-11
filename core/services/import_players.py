def load_user_data(restore_string: str):
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