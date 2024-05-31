from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.postgres.fields import JSONField

class CustomUser(AbstractUser):
    display_name = models.CharField(max_length=255, null=True, blank=True)
    avatar = models.URLField(max_length=200, null=True, blank=True)
    friends = JSONField(default=list)  # list of friend usernames
    stats = JSONField(default=dict)  # custom struct for user stats
    match_history = JSONField(default=list)  # array of custom structs for match history
    two_factor_auth_enabled = models.BooleanField(default=False)
    
    def __str__(self):
        return self.username

    class Meta:
        db_table = 'auth_user'
# You may need to add this in your settings.py
# AUTH_USER_MODEL = 'yourapp.CustomUser'
