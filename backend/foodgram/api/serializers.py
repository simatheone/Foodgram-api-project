from rest_framework import serializers
from django.shortcuts import get_list_or_404

from recipes.models import Ingredient, Tag
from users.models import CustomUser, Subscription


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


class CustomUserSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField(
        read_only=True
    )

    class Meta:
        model = CustomUser
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        subscription = Subscription.objects.filter(user_id=obj.id)
        if subscription: return True
        return False
