import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.safestring import mark_safe
from django.utils import timezone

class Player(models.Model):
    name = models.CharField(max_length=100)
    gender = models.CharField(
        max_length=10,
        choices=[("M", "Male"), ("F", "Female")],
        default="M"
    )

    mu = models.DecimalField(max_digits=5, decimal_places=2,)
    sigma = models.DecimalField(max_digits=5, decimal_places=2, default=4)

    @staticmethod
    def shorten_name(name):
        parts = name.split()

        if len(parts) >= 2:
            # Take first 4 letters of first name + first 2 letters of second name
            return f"{parts[0][:4]}. {parts[1][:2]}."

        if len(name) > 7:
            return f"{name[:6]}.."

        return name

    def __str__(self):
        return self.name

    @staticmethod
    def format_name_gender(name, is_female, shorten_name=False):
        color_class = (
            "text-pink-300 font-medium"
            if is_female
            else "text-blue-300 font-medium"
        )

        if shorten_name and len(name) > 7:
            name_short = Player.shorten_name(name)
        else:
            name_short = name

        return f'<span class="{color_class}">{name_short}</span>'
        

    def name_coloured(self, shorten_name=False):
        return self.format_name_gender(self.name, self.gender == "F", shorten_name=shorten_name)
    

    def get_name_with_mu(self):
        
        return mark_safe(f"{self.name_coloured()}<sup>{self.mu}</sup>")
    

    def get_name(self):
        return mark_safe(self.name_coloured())
    

    
    def get_name_with_mu_short(self):
        
        return mark_safe(f"{self.name_coloured(shorten_name=True)}<sup>{self.mu}</sup>")
    

    def get_name_short(self):
        return mark_safe(self.name_coloured(shorten_name=True))
    
    

    
class Session(models.Model):

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    date = models.DateField(default=timezone.now)
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
    started_at = models.DateTimeField(default=timezone.now, null=True)
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


class GenderPair(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="gender_pairs")
    
    player1_s = models.ForeignKey(
        PlayerSession, 
        on_delete=models.CASCADE, 
        related_name="gender_pair_as_player1"
    )
    gender = models.CharField(
        max_length=10,
        choices=[("M", "MEN"), ("F", "WOMEN")],
    )

    @staticmethod
    def format_gender(gender):
        is_women = gender == "F"

        color_class = (
            "text-pink-300 font-medium"
            if is_women
            else "text-blue-300 font-medium"
        )

        display_name = "WOMEN" if is_women else "MEN"

        return f'<span class="{color_class}">{display_name}</span>'


    def __str__(self):
        return "WOMEN" if self.gender == "F" else "MEN"


    @property
    def get_name(self):
        return mark_safe(f"{self.player1_s.player.name_coloured()} & {self.format_gender(self.gender)}")


class MatchmakingConfig(models.Model):
    """
    Singleton config for matchmaking weights and parameters.
    Admins can edit these from the Django admin panel.
    """
    # Weights
    games_played_weight = models.PositiveIntegerField(default=25, help_text="Playtime fairness")
    fairness_weight = models.PositiveIntegerField(default=10, help_text="Overall match skill fairness (win differential)")
    played_with_weight = models.PositiveIntegerField(default=7, help_text="Teammate repeat penalty")
    played_against_weight = models.PositiveIntegerField(default=4, help_text="Opponent repeat penalty")
    gender_weight = models.PositiveIntegerField(default=2, help_text="Gender balance")
    skill_difference_weight = models.PositiveIntegerField(default=3, help_text="Intra-team skill gap penalty")

    class Meta:
        verbose_name = "Matchmaking Configuration"
        verbose_name_plural = "Matchmaking Configuration"

    def __str__(self):
        return "Matchmaking Configuration (Singleton)"

    def clean(self):
        if MatchmakingConfig.objects.exclude(pk=self.pk).exists():
            raise Exception("Only one MatchmakingConfig record is allowed.")

    def save(self, *args, **kwargs):
        self.pk = 1  # Force primary key to 1
        super().save(*args, **kwargs)

    @classmethod
    def get_config(cls):
        """Safe singleton getter"""
        config, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'games_played_weight': 25,
                'fairness_weight': 10,
                'skill_difference_weight': 4,
                'played_with_weight': 7,
                'played_against_weight': 4,
                'gender_weight': 2,
            }
        )
        return config
    

class ClubConfig(models.Model):
    key =  models.CharField(max_length=100, unique=True)
    value = models.CharField(max_length=100)


    @classmethod
    def get(cls, key, default=None):
        obj, _ = cls.objects.get_or_create(
                key=key,
                defaults={"value": default or ""}

            )
        return obj.value
    