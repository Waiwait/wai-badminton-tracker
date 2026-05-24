from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Club, Session, Player, PlayerSession, Match, MatchParticipant

@login_required
def home(request):
    clubs = Club.objects.all()
    active_sessions = Session.objects.filter(active=True).select_related('club')
    context = {
        'clubs': clubs,
        'active_sessions': active_sessions,
    }
    return render(request, 'core/home.html', context)


@login_required
def club_dashboard(request, club_id):
    club = get_object_or_404(Club, club_id=club_id)
    active_sessions = Session.objects.filter(club=club, active=True)
    players = club.players.all()
    
    context = {
        'club': club,
        'active_sessions': active_sessions,
        'players': players,
    }
    return render(request, 'core/club_dashboard.html', context)


@login_required
def start_session(request, club_id):
    club = get_object_or_404(Club, club_id=club_id)
    if request.method == 'POST':
        venue = request.POST.get('venue', '')
        session = Session.objects.create(
            club=club,
            venue=venue,
            active=True
        )
        return redirect('session_detail', session_id=session.session_id)
    return render(request, 'core/start_session.html', {'club': club})


@login_required
def session_detail(request, session_id):
    session = get_object_or_404(Session, session_id=session_id)
    players_in_session = PlayerSession.objects.filter(session=session).select_related('player')
    matches = session.matches.all().prefetch_related('matchparticipant_set')
    
    context = {
        'session': session,
        'players_in_session': players_in_session,
        'matches': matches,
        'available_players': session.club.players.exclude(playersession__session=session)
    }
    return render(request, 'core/session_detail.html', context)


@login_required
def add_player_to_session(request, session_id):
    session = get_object_or_404(Session, session_id=session_id)
    if request.method == 'POST':
        player_id = request.POST.get('player_id')
        player = get_object_or_404(Player, player_id=player_id)
        PlayerSession.objects.get_or_create(session=session, player=player)
    return redirect('session_detail', session_id=session.session_id)


@login_required
def start_match(request, session_id):
    session = get_object_or_404(Session, session_id=session_id)
    if request.method == 'POST':
        court = request.POST.get('court')
        player_ids = request.POST.getlist('players')
        
        if len(player_ids) != 4:
            pass  # Handle in UI
            
        match = Match.objects.create(
            session=session,
            court=int(court) if court else None
        )
        
        for i, pid in enumerate(player_ids[:4]):
            team = 1 if i < 2 else 2
            player = get_object_or_404(Player, player_id=pid)
            MatchParticipant.objects.create(
                match=match,
                player=player,
                team=team
            )
        return redirect('session_detail', session_id=session.session_id)
    
    players_in_session = PlayerSession.objects.filter(session=session)
    return render(request, 'core/start_match.html', {
        'session': session,
        'players': players_in_session
    })
