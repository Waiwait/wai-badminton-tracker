from ..models import PlayerSession

def add_player(session, player):
    obj, _ = PlayerSession.objects.get_or_create(
        session=session,
        player=player
    )
    return obj


def remove_player(session, player):
    PlayerSession.objects.filter(
        session=session,
        player=player
    ).delete()