from django.contrib import admin

from foodgram.settings import EMPTY_VALUE_ADMIN_PANEL
from .models import CustomUser, Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
  list_display = ('user', 'author')
  list_display_links = ('user',)
  list_editable = ('author',)
  list_filter = ('user',)
  search_fields = ('user', 'author')
  empty_value_display = EMPTY_VALUE_ADMIN_PANEL


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
  list_display = (
    'id',
    'username',
    'email',
    'first_name',
    'last_name',
    'password',
    'role',
    'is_superuser',
    'is_active',
    'date_joined',
    'is_staff'
  )
  list_editable = (
    'username',
    'email',
    'first_name',
    'last_name',
    'password',
    'role',
    'is_superuser',
    'is_active',
    'is_staff'
  )
  list_filter = (
    'username',
    'email',
    'first_name',
    'last_name',
    'role',
    'date_joined',
  )
  search_fields = ('username', 'email', 'first_name')
  empty_value_display = EMPTY_VALUE_ADMIN_PANEL