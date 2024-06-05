from django.db import models

# Create your models here.

class Player(models.Model):
    # userId relational connection to the user modul/ database
    name = models.CharField(max_length=40)
    points = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    
    def to_dict(self):
        return {
            'name': self.name,
            'points': self.points,
            'wins': self.wins,
            'losses': self.losses,
        }
       

    # To display the name of the teacher in the admin panel instead of the object name
    def __str__(self):
      return self.name
    
class Game(models.Model):
    id = models.AutoField(primary_key=True)
    player1 = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='player1')
    player2 = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='player2')
    player1_score = models.IntegerField(default=0)
    player2_score = models.IntegerField(default=0)
    winner = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='winner')
    loser = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='loser')

    date = models.DateTimeField(auto_now_add=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'player1': self.player1.name,
            'player2': self.player2.name,
            'player1_score': self.player1_score,
            'player2_score': self.player2_score,
            'winner': self.winner.name,
            'loser': self.loser.name,
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S'),
        }

    # To display the name of the teacher in the admin panel instead of the object name
    def __str__(self):
      return self.player1.name + " vs " + self.player2.name + " (" + self.winner.name + ")"
