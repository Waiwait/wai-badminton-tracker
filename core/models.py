import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.safestring import mark_safe

class Player(models.Model):
    name = models.CharField(max_length=100)
    gender = models.CharField(
        max_length=10,
        choices=[("M", "Male"), ("F", "Female")],
        default="M"
    )

    mu = models.DecimalField(max_digits=5, decimal_places=2,)
    sigma = models.DecimalField(max_digits=5, decimal_places=2, default=3)

    def __str__(self):
        return f"{self.name}"
    
    @staticmethod
    def format_name_gender(name, is_female):
        color_class = "text-pink-300 font-medium" if is_female else "text-blue-300 font-medium"
        return f'<span class="{color_class}">{name}</span>'
    

    def name_coloured(self):
        return self.format_name_gender(self.name, self.gender == "F")

    def get_name_with_mu(self):
        
        return mark_safe(f"{self.name_coloured()}<sup>{self.mu}</sup>")
    

    def get_name(self):
        return mark_safe(self.name_coloured())
    
    

    
class Session(models.Model):

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    date = models.DateField(auto_now_add=True)
    venue = models.CharField(max_length=100, blank=True, default="Main Hall")
    active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.active:
            # deactivate all other sessions
            Session.objects.exclude(pk=self.pk).update(active=False)

        super().save(*args, **kwargs)


class PlayerSession(models.Model):
    
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    games_skipped = models.IntegerField(default = 0)
    games_played = models.IntegerField(default = 0)
    pause = models.BooleanField(default=False)

    class Meta:
        unique_together = ("session", "player")


class Court(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="courts")
    number = models.IntegerField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"Court {self.number}"

class Match(models.Model):
    court = models.ForeignKey(
        Court, 
        on_delete=models.CASCADE, 
        related_name="matches"
    )
    finished = models.BooleanField(default=False)

    def __str__(self):
        return f"Match {self.id} on Court {self.court.number if self.court else '?'}"

    class Meta:
        ordering = ['-id']


class MatchTeam(models.Model):
    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name="teams"          # match.teams.all()
    )
    team_number = models.IntegerField(choices=[(1, "Team 1"), (2, "Team 2")])
    is_winner = models.BooleanField(default=False)
    score = models.IntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(30)
        ]
    )

    class Meta:
        unique_together = ("match", "team_number")
        ordering = ['team_number']

    def __str__(self):
        return f"Match {self.match_id} - Team {self.team_number} ({self.score})"


class MatchParticipant(models.Model):
    """Player belonging to a team in a match"""
    match_team = models.ForeignKey(
        MatchTeam,
        on_delete=models.CASCADE,
        related_name="participants"
    )
    player = models.ForeignKey(Player, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("match_team", "player")

    def __str__(self):
        return f"{self.player} - {self.match_team}"


class UpcomingMatch(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    # index of a match queue
    value = models.DecimalField(max_digits=5, decimal_places=3,)
    # should be id1,id2,id3,id4 (first 2 should be team1, last2 should be team2)
    player_ids = models.CharField(max_length=100)
    


class Pair(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="pairs")
    
    player1_s = models.ForeignKey(
        PlayerSession, 
        on_delete=models.CASCADE, 
        related_name="pair_as_player1"
    )
    player2_s = models.ForeignKey(
        PlayerSession, 
        on_delete=models.CASCADE, 
        related_name="pair_as_player2"
    )


    @property
    def get_name(self):
        return mark_safe(f"{self.player1_s.player.name_coloured()} & {self.player2_s.player.name_coloured()}")
