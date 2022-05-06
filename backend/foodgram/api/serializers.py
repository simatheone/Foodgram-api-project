import imghdr
import uuid
import base64
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from django.db.models import Count
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (
    Ingredient, Recipe, Tag, ShoppingCart, RecipeTag,
    RecipeIngredient, IngredientAmount, Favorite
)
from users.models import CustomUser, Subscription


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer for the TagViewSet.
    """
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')

    def to_internal_value(self, data):
        tag = get_object_or_404(Tag, pk=data)
        return tag


class IngredientSerializer(serializers.ModelSerializer):
    """
    Serializer for the IngredientViewSet.
    """
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class CustomUserSerializer(serializers.ModelSerializer):
    """Serializer for CustomUserViewset."""
    is_subscribed = serializers.SerializerMethodField(
        read_only=True
    )

    class Meta:
        model = CustomUser
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user= self.context['request'].user
        subscribed = Subscription.objects.filter(
            user=user, author=obj
        )
        if subscribed: return True
        return False


class Base64ImageField(serializers.ImageField):
    """Serialier for ImageField encoded in Base64."""
    def to_internal_value(self, data):
        if isinstance(data, str):
            if 'data:' in data and ';base64,' in data:
                header, data = data.split(';base64,')
            try:
                decoded_file = base64.b64decode(data)
            except TypeError:
                raise TypeError('Invalid image format')
        
            file_name = str(uuid.uuid4())[:13]
            file_extension = self.get_file_extension(file_name, decoded_file)
            complete_file = f'{file_name}.{file_extension}'
            data = ContentFile(decoded_file, name=complete_file)
        return super(Base64ImageField, self).to_internal_value(data)

    def get_file_extension(self, file_name, decoded_file):
        """Method which gets the extension of image file."""
        extension = imghdr.what(file_name, decoded_file)
        if extension == 'jpeg':
            extension = 'jpg'
        return extension


class TagsListingField(serializers.RelatedField):
    def to_internal_value(self, data):
        tag = get_object_or_404(Tag, pk=data)
        return tag

    def to_representation(self, value):
        data_tag = {
            'id': value.id,
            'name': value.name,
            'color': value.color,
            'slug': value.slug 
        }
        return data_tag


class IngredientAmountSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngredientAmount
        fields = ('ingredient', 'amount')
        validation = [
            UniqueTogetherValidator(
                queryset=IngredientAmount.objects.all(),
                fields=('ingredient', 'amount'),
                message='Нельзя добавить одниковые ингредиента с одинаковым количеством.'
            )
        ]

    def to_internal_value(self, data):
        ingredient_id = data.get('id')
        amount = data.get('amount')
        ingredient = get_object_or_404(
            Ingredient,
            id=ingredient_id,
        )
        data = {
            'id': ingredient.id,
            'name': ingredient.name,
            'measurement_unit': ingredient.measurement_unit,
            'amount': amount
        }
        return data

    def to_representation(self, value):
        amount_obj = get_object_or_404(
            IngredientAmount, ingredient=value
        )
        ingredients = {
            'id': value.id,
            'name': value.name,
            'measurement_unit': value.measurement_unit,
            'amount': amount_obj.amount,
        }
        return ingredients

class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for RecipeViewSet."""
    author = CustomUserSerializer(read_only=True)
    tags = TagsListingField(
        queryset=Tag.objects.all(), many=True, required=True
    )
    tag = TagSerializer(many=True)
    ingredients = IngredientAmountSerializer(
        many=True, required=True
    )
    # queryset=IngredientAmount.objects.all(), 

    # ingredients = IngredientAmountSerializer(
    #     many=True, required=True
    # )
    image = Base64ImageField(
        max_length=None, use_url=True, required=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time',  
        )
        read_only_fields = ('id', 'is_favorited', 'is_in_shopping_cart')
        validation = [
            UniqueTogetherValidator(
                queryset=IngredientAmount.objects.all(),
                fields=('name', 'text'),
                message='Нельзя добавить два одиноквых рецепта.'
            )
        ]

    def get_is_favorited(self, obj):
        request_user = self.context['request'].user
        favorite = Favorite.objects.filter(
            recipe=obj, user=request_user
        )
        if favorite: return True
        return False

    def get_is_in_shopping_cart(self, obj):
        request_user = self.context['request'].user
        shopping_cart = ShoppingCart.objects.filter(
            recipe=obj, user=request_user
        )
        if shopping_cart: return True
        return False

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        for tag in tags:
            RecipeTag.objects.create(
                tag=tag, recipe=recipe
            )
        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            amount = ingredient['amount']
            RecipeIngredient.objects.create(
                recipe=recipe, ingredient_id=ingredient_id
            )
            IngredientAmount.objects.create(
                ingredient_id=ingredient_id, amount=amount
            )
        return recipe


class FavoriteSerializer(serializers.ModelSerializer):
    """
    Serializer for RecipeViewSet. 
    Route: .../api/recipes/1/favorite/
    """
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='В избранное нельзя добавить два одинаковых рецепта.'
            )
        ]

    def to_representation(self, value):
        recipe = get_object_or_404(Recipe, pk=value.recipe_id)
        image = self.context['request'].build_absolute_uri(recipe.image.url)
        return {
            'id': recipe.id,
            'name': recipe.name,
            'image': image,
            'cooking_time': recipe.cooking_time
        }


class ShoppingCartSerializer(FavoriteSerializer):
    """
    """
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='В список покупок нельзя добавить два одинаковых рецепта.'
            )
        ]


class RecipeField(serializers.SlugRelatedField):
    def to_internal_value(self, data):
        print("INTERNAL VALUE!!!!!")
        print(data)

    def to_representation(self, value):
        print('RecipeField TO REPR')
        print(value)


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    """
    recipes_count = serializers.SerializerMethodField(
        read_only=True
    )
    recipes = RecipeField(
        slug_field='name',
        read_only=True
    )
    author = CustomUserSerializer(read_only=True)
    class Meta:
        model = Subscription
        fields = ('author', 'recipes_count', 'recipes')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message='Нельзя дважды подписаться на одного автора.'
            )
        ]

    def create(self, validated_data):
        print('CREATE VALIDATED DATA !!!!!!!!!!!')
        print(validated_data)
        return Subscription.objects.create(**validated_data)

    def get_recipes_count(self, obj):
        print('get_recipes_count HERE!!!!!!!!!!!!!!!!')
        print(obj)
        """
        Method field.
        Method returns the count of the author's recipes.
        """
        results = Recipe.objects.filter(author=obj.author).aggregate(
            count_recipes=Count('name')
        )
        return results['count_recipes']
