from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """Custom user model"""
    email = models.EmailField(unique=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')], null=True, blank=True)

    def __str__(self):
        return self.username


class Club(models.Model):
    club_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    # owner or admin can be linked via User later if needed

    def __str__(self):
        return self.name


class Player(models.Model):
    player_id = models.AutoField(primary_key=True)
    MMR = models.IntegerField(default=100)
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='players')
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='player_profile', null=True, blank=True)

    def __str__(self):
        return f"{self.user.username if self.user else 'Player'} - {self.club.name}"


class Session(models.Model):
    session_id = models.AutoField(primary_key=True)
    date = models.DateField(auto_now_add=True)
    venue = models.CharField(max_length=100, blank=True)
    active = models.BooleanField(default=True)
    courts = models.CharField(max_length=50, default="1,2,3,4")  # e.g. courts available
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='sessions')

    def __str__(self):
        return f"Session {self.session_id} - {self.date}"


class PlayerSession(models.Model):
    player_session_id = models.AutoField(primary_key=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    pause = models.BooleanField(default=False)

    class Meta:
        unique_together = ('session', 'player')

    def __str__(self):
        return f"{self.player} in {self.session}"


class Match(models.Model):
    match_id = models.AutoField(primary_key=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='matches')
    court = models.IntegerField(null=True, blank=True)
    score = models.CharField(max_length=20, blank=True)  # e.g. "21-19"
    winning_team = models.IntegerField(choices=[(1, 'Team 1'), (2, 'Team 2')], null=True, blank=True)
    finished = models.BooleanField(default=False)

    def __str__(self):
        return f"Match {self.match_id} on Court {self.court}"


class MatchParticipant(models.Model):
    match_participant_id = models.AutoField(primary_key=True)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    team = models.IntegerField(choices=[(1, 'Team 1'), (2, 'Team 2')])

    def __str__(self):
        return f"{self.player} in Match {self.match_id} Team {self.team}"
