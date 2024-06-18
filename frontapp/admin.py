from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Friendship, Game
from django.contrib.auth.models import User
from django import forms
from django.db.models import Q

class CustomUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(CustomUserForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

class GameInline(admin.TabularInline):
    model = Game
    extra = 0
    verbose_name = "Game"
    verbose_name_plural = "Games"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.parent_model == CustomUser:
            user_id = request.resolver_match.kwargs.get('object_id')
            return qs.filter(Q(player1_id=user_id) | Q(player2_id=user_id) | Q(winner_id=user_id))
        return qs

    fk_name = 'player1'  # Diese Beziehung angeben, um den Fehler zu umgehen

class CustomUserAdmin(UserAdmin):
    form = CustomUserForm
    list_display = [field.name for field in CustomUser._meta.fields]
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {
            'classes': ('wide',),
            'fields': tuple(field.name for field in CustomUser._meta.fields if field.name not in [f.name for f in User._meta.fields]),
        }),
    )
    fieldsets = UserAdmin.fieldsets + (
        (None, {
            'fields': tuple(field.name for field in CustomUser._meta.fields if field.name not in [f.name for f in User._meta.fields]),
        }),
    )
    inlines = [GameInline]  # Hier fügen wir den Inline-Admin hinzu

class FriendshipAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'accepted')
    list_editable = ('accepted',)
    
class GameAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Game._meta.fields]

admin.site.register(Friendship, FriendshipAdmin)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Game, GameAdmin)
