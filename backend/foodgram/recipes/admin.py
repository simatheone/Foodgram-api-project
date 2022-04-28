from django.contrib import admin
from django.db.models import Count

from foodgram.settings import EMPTY_VALUE_ADMIN_PANEL
from .models import (
    Favorite, Ingredient, Recipe, RecipeIngredient,
    RecipeTag, ShoppingCart, Tag
)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user', 'recipe')
    empty_value_display = EMPTY_VALUE_ADMIN_PANEL


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name',)
    empty_value_display = EMPTY_VALUE_ADMIN_PANEL


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'count_recipe_in_favorites')
    list_filter = ('name', 'author', 'tag')
    search_fields = ('name', 'author')
    empty_value_display = EMPTY_VALUE_ADMIN_PANEL

    def count_recipe_in_favorites(self, obj):
        result = Favorite.objects.annotate(recipe=Count('recipe'))
        return len(result)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient')
    list_display_links = ('recipe', 'ingredient')
    list_filter = ('recipe', 'ingredient')
    search_fields = ('recipe', 'ingredient')
    empty_value_display = EMPTY_VALUE_ADMIN_PANEL


@admin.register(RecipeTag)
class RecipeTagAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'tag')
    list_display_links = ('recipe', 'tag')
    list_filter = ('recipe', 'tag')
    search_fields = ('recipe', 'tag')
    empty_value_display = EMPTY_VALUE_ADMIN_PANEL


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user', 'recipe')
    empty_value_display = EMPTY_VALUE_ADMIN_PANEL


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    list_display_links = ('name', 'color', 'slug')
    list_filter = ('name',)
    search_fields = ('name', 'slug', 'color')
    prepopulated_fields = {'slug': ('name',)}
    empty_value_display = EMPTY_VALUE_ADMIN_PANEL
