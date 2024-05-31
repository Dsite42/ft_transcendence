from django.contrib.auth.models import AbstractUser ,Group, Permission
from django.db import models
from django.db.models import JSONField


class CustomUser(AbstractUser):
    display_name = models.CharField(max_length=255, null=True, blank=True)
    avatar = models.URLField(max_length=200, null=True, blank=True)
    friends = JSONField(default=list)  # list of friend usernames
    stats = JSONField(default=dict)  # custom struct for user stats
    match_history = JSONField(default=list)  # array of custom structs for match history
    two_factor_auth_enabled = models.BooleanField(default=False)
    
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
# You may need to add this in your settings.py
# AUTH_USER_MODEL = 'yourapp.CustomUser'
