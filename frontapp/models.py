from django.db import models

# Create your models here.

class Player(models.Model):
    # userId relational connection to the user modul/ database
    name = models.CharField(max_length=40)
    points = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    
    # To display the name of the teacher in the admin panel instead of the object name
    def __str__(self):
      return self.name
