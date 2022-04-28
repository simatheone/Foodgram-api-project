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
