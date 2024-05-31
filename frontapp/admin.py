from django.contrib import admin

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django.contrib.auth.models import User
from django import forms

class CustomUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(CustomUserForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

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

admin.site.register(CustomUser, CustomUserAdmin)