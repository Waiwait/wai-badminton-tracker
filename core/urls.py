from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('club/<int:club_id>/', views.club_dashboard, name='club_dashboard'),
    path('session/start/<int:club_id>/', views.start_session, name='start_session'),
    path('session/<int:session_id>/', views.session_detail, name='session_detail'),
    path('session/<int:session_id>/add-player/', views.add_player_to_session, name='add_player_to_session'),
    path('session/<int:session_id>/start-match/', views.start_match, name='start_match'),
]
