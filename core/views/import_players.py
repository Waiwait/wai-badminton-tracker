from ..services.import_players import load_user_data
from ..services.permissions import is_admin
from ..models import Player


from django.shortcuts import render
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import user_passes_test


@user_passes_test(is_admin)
def load_players_page(request):
    context = {}
    
    if request.method == 'POST':
        restore_string = request.POST.get('restore_string', '').strip()
        
        if not restore_string:
            messages.error(request, "Please paste the restore string")
            return render(request, 'load_players.html', context)

        try:
            players_data = load_user_data(restore_string)

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

            context['players'] = players_data
            context['created'] = created

            messages.success(request, 
                f"Successfully created {created} new players.")

        except Exception as e:
            messages.error(request, f"Error processing data: {str(e)}")

    return render(request, 'import/import_players.html', context)