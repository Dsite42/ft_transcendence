from django.contrib.auth.models import AbstractUser ,Group, Permission
from django.db import models
from django.db.models import JSONField


class CustomUser(AbstractUser):
    display_name = models.CharField(max_length=255, null=True, blank=True)
    avatar = models.URLField(max_length=200, null=True, blank=True)
    stats = JSONField(default=dict, null=True, blank=True )  # custom struct for user stats
    match_history = JSONField(default=list,  null=True, blank=True)  # array of custom structs for match history
    two_factor_auth_enabled = models.BooleanField(default=False)
    last_active = models.DateTimeField(null=True, blank=True)
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )
    #Friendship Functions

    def get_friends(self):
        # Get all friendships where the friend request has been accepted
        accepted_friendships = self.friendships_sent.filter(accepted=True) | self.friendships_received.filter(accepted=True)
        
        # Get the friends from the friendships
        friends = [friendship.to_user for friendship in accepted_friendships if friendship.to_user != self] + \
                [friendship.from_user for friendship in accepted_friendships if friendship.from_user != self]
        
        return friends

    def get_pending_friend_requests(self):
        
        pending_friendships = self.friendships_received.filter(accepted=False)

        pending_friends = [friendship.from_user for friendship in pending_friendships]
        
        return pending_friends

    def add_friend_request(self, new_friend):
        # Check if the friend is not the user itself
        if new_friend != self:
            # Check if the friend is not already a friend
            if new_friend not in self.get_friends():
                # Create a new friendship
                friendship = Friendship(from_user=self, to_user=new_friend, accepted=False)
                friendship.save()
                return True
        return False
    
    def accept_friend_request(self, friend):
        # Get the friendship where the friend is the sender
        friendship = self.friendships_received.filter(from_user=friend).first()
        
        # Check if the friendship exists
        if friendship:
            # Accept the friend request
            friendship.accepted = True
            friendship.save()
            return True
        return False

    def remove_friend(self, friend):
        # Get the friendship where the friend is the sender
        friendship = self.friendships_sent.filter(to_user=friend).first() or self.friendships_received.filter(from_user=friend).first()
        
        # Check if the friendship exists
        if friendship:
            friendship.delete()
            return True
        return False
    
    # ----------------------------

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'auth_user'


class CustomUserGroup(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

class CustomUserPermission(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

class Friendship(models.Model):
    from_user = models.ForeignKey(CustomUser, related_name='friendships_sent', on_delete=models.CASCADE)
    to_user = models.ForeignKey(CustomUser, related_name='friendships_received', on_delete=models.CASCADE)
    accepted = models.BooleanField(default=False)
    popup_shown = models.BooleanField(default=False)
    class Meta:
        unique_together = ('from_user', 'to_user')


#Import from Dashboards

# from django.db import models

# # Create your models here.

# class Player(models.Model):
#     # userId relational connection to the user modul/ database
#     name = models.CharField(max_length=40)
#     points = models.IntegerField(default=0)
#     wins = models.IntegerField(default=0)
#     losses = models.IntegerField(default=0)
    
#     def to_dict(self):
#         return {
#             'name': self.name,
#             'points': self.points,
#             'wins': self.wins,
#             'losses': self.losses,
#         }
       

#     # To display the name of the teacher in the admin panel instead of the object name
#     def __str__(self):
#       return self.name
    
class Game(models.Model):
    game_id = models.AutoField(primary_key=True)
    player1 = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='player1')
    player2 = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='player2')
    p1_wins = models.IntegerField(default=0)
    p2_wins = models.IntegerField(default=0)
    winner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='winner')

    date = models.DateTimeField(auto_now_add=True)
    
    def to_dict(self):
        return {
            'game_id': self.id,
            'player1': self.player1.username,
            'player2': self.player2.username,
            'p1_wins': self.p1_wins,
            'player2_score': self.player2_score,
            'winner': self.winner.username,
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S'),
        }

    # To display the name of the teacher in the admin panel instead of the object name
    def __str__(self):
      return self.player1.username + " vs " + self.player2.username + " (" + self.winner.username + ")"