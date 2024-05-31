from django.contrib import admin

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    list_display = [field.name for field in CustomUser._meta.fields]

admin.site.register(CustomUser, CustomUserAdmin)