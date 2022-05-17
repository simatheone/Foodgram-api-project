from django.contrib import admin

from foodgram.settings import EMPTY_VALUE_ADMIN_PANEL

from .models import CustomUser, Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin panel for Subscription model."""
    list_display = ('id', 'user', 'author', 'subscribe_date')
    search_fields = ('user__username', 'author__username')
    empty_value_display = EMPTY_VALUE_ADMIN_PANEL


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    """Admin panel for CustomUser model."""
    list_display = (
        'id', 'username', 'email', 'first_name',
        'last_name', 'password', 'role',
        'is_superuser', 'is_active', 'date_joined',
        'is_staff'
    )
    list_editable = (
        'username', 'email', 'first_name',
        'last_name', 'password', 'role',
        'is_superuser', 'is_active', 'is_staff'
    )
    list_filter = (
        'email', 'first_name',
        'role', 'date_joined'
    )
    search_fields = ('username', 'email', 'first_name')
    empty_value_display = EMPTY_VALUE_ADMIN_PANEL
