import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Player(models.Model):
    name = models.CharField(max_length=100)
    gender = models.CharField(
        max_length=10,
        choices=[("M", "Male"), ("F", "Female")],
        default="M"
    )
    strength = models.IntegerField(
        default=50,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(100)
        ]
    )

    def __str__(self):
        return f"{self.name} ({self.strength}"


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
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="matches")
    court = models.ForeignKey(Court, null=True, blank=True, on_delete=models.SET_NULL, related_name="matches")
    score = models.CharField(max_length=50, blank=True)
    winning_team = models.IntegerField(null=True, blank=True, choices=[(1, "Team 1"), (2, "Team 2")])
    finished = models.BooleanField(default=False)

    def __str__(self):
        return f"Match {self.id} on Court {self.court}"
    

class MatchParticipant(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    team = models.IntegerField(choices=[(1, "Team 1"), (2, "Team 2")])
