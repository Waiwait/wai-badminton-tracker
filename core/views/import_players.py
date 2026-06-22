from ..services.import_players import load_user_data_superbadders, load_user_data_ebadders, create_players
from ..services.permissions import is_admin

from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test


@user_passes_test(is_admin)
def load_players_page_superbadders(request):
    context = {}
    
    if request.method == 'POST':
        restore_string = request.POST.get('restore_string', '').strip()
        
        if not restore_string:
            messages.error(request, "Please paste the restore string")
            return render(request, 'load_players.html', context)

        try:
            players_data = load_user_data_superbadders(restore_string)


            created = create_players(players_data)

            messages.success(request, 
                f"Successfully created {created} new players.")
            
            context['players'] = players_data
            context['created'] = created

        except Exception as e:
            messages.error(request, f"Error processing data: {str(e)}")

    return render(request, 'import/import_players_superbadders.html', context)


@user_passes_test(is_admin)
def load_players_page_ebadders(request):
    context = {}
    
    if request.method == 'POST':
        uploaded_file = request.FILES["club_file"]
        restore_string =  uploaded_file.read().decode("utf-8")

        try:
            players_data = load_user_data_ebadders(restore_string)


            created = create_players(players_data)

            messages.success(request, 
                f"Successfully created {created} new players.")
            
            context['players'] = players_data
            context['created'] = created

        except Exception as e:
            messages.error(request, f"Error processing data: {str(e)}")

    return render(request, 'import/import_players_ebadders.html', context)




