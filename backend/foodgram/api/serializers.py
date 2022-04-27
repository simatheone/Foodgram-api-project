from rest_framework import serializers

from recipes.models import Ingredient, Tag


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer for the TagViewSet.
    """

    class Meta:
        model = Tag
        fileds = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """
    Serializer for the IngredientViewSet.
    """

    class Meta:
        model = Ingredient
        fileds = ('id', 'name', 'measurement_unit')
