
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test

from ..services.permissions import is_admin
from ..services.renders import render_payment_data


@user_passes_test(is_admin)
def render_payment(request):
    return render(
        request,
        "payment/payment.html",
        render_payment_data(request),
    )


def render_outstanding_payment(request):
    return render(
        request,
        "payment/payment.html",
        render_payment_data(request, show_missing_only=True, show_admin_panel=False),
    )