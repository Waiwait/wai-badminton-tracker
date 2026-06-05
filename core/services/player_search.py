from ..models import Player, PlayerSession

def search_players(query, limit=10):
    return Player.objects.filter(
        name__icontains=query
    )[:limit]


def search_available_players(query, session, limit=10):
    already_in_session = PlayerSession.objects.filter(
        session=session
    ).values_list("player_id", flat=True)

    return Player.objects.filter(
        name__icontains=query
    ).exclude(
        id__in=already_in_session
    )[:limit]