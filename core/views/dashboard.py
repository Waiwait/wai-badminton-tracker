
from ..models import Session
from ..services.permissions import is_admin

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import user_passes_test

def is_admin(user):
    return user.is_superuser


def session_detail(request, uuid):
    session = get_object_or_404(Session, uuid=uuid)
    return render(request, "match/session_dashboard.html", {
        "session": session,
        "show_admin_panel": is_admin(request.user),
    })


@user_passes_test(is_admin)
def admin_dashboard(request, uuid):
    session = get_object_or_404(Session, uuid=uuid)
    return render(request, "match/partials/admin_dashboard.html", {
        "session": session,
    })