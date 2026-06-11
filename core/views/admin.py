from ..services.permissions import is_admin
from ..models import Session
from ..services.renders import render_players

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import user_passes_test



@user_passes_test(is_admin)
def admin_players(request, uuid):
    session = get_object_or_404(Session, uuid=uuid)

    return render(request, "match/partials/admin_players.html", render_players(session))

