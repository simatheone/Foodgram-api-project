from django_filters import FilterSet
from django_filters.filters import (CharFilter, ModelChoiceFilter,
                                    ModelMultipleChoiceFilter, NumberFilter)
from recipes.models import Ingredient, Recipe, Tag
from users.models import CustomUser


class RecipeFilter(FilterSet):
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    author = ModelChoiceFilter(
        queryset=CustomUser.objects.all()
    )
    is_favorited = NumberFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = NumberFilter(
        method='filter_is_in_shopping_cart'
    )

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value == 1:
            queryset = Recipe.objects.filter(favorite_recipe__user=user)
        if value == 0:
            queryset = Recipe.objects.all().exclude(
                favorite_recipe__user=user
            )
        return queryset.order_by('-pk')

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value == 1:
            queryset = Recipe.objects.filter(shopping_cart__user=user)
        if value == 0:
            queryset = Recipe.objects.all().exclude(
                shopping_cart__user=user
            )
        return queryset.order_by('-pk')

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')


class IngredientFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Ingredient
        fields = ('name',)
