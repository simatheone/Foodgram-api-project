from drf_base64.fields import Base64ImageField
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from django.db.models import Count
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import(
    Favorite, Ingredient, Recipe,
    RecipeIngredientAmount, ShoppingCart, Tag
)
from users.models import CustomUser, Subscription
from foodgram.settings import IMAGE_NAME_LEN


class IsSubscribedMethod:

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return user.sub_user.filter(author=obj).exists()
        return False


class CustomUserSerializer(serializers.ModelSerializer,
                           IsSubscribedMethod):
    """Serializer for CustomUserViewset."""
    is_subscribed = serializers.SerializerMethodField(
        read_only=True
    )

    class Meta:
        model = CustomUser
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'password', 'is_subscribed'
        )
        extra_kwargs = {'password': {'write_only': True}}


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer for the TagViewSet.
    """

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """
    Serializer for the IngredientViewSet.
    """

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientAmountSerializer(serializers.ModelSerializer):
    """
    Serializes ingredient fields + amount in RecipeReadSerializer.
    """
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredientAmount
        fields = (
            'id', 'name', 'measurement_unit', 'amount'
        )


class IngredientAmountSerializer(serializers.ModelSerializer):
    """
    Serializes ingredient, amount fields in RecipeWriteSerializer.
    """
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredientAmount
        fields = ('id', 'amount')


class AuthorForRecipeSerializer(serializers.ModelSerializer,
                                IsSubscribedMethod):
    """
    Serializes the author of recipe. 
    Uses in RecipeReadSerializer.
    """
    is_subscribed = serializers.SerializerMethodField(
        read_only=True
    )

    class Meta:
        model = CustomUser
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed'
        )


class RecipeReadSerializer(serializers.ModelSerializer):
    """Read Serializer for RecipeViewSet."""
    author = AuthorForRecipeSerializer(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    tags = TagSerializer(
        many=True, read_only=True
    )
    ingredients = RecipeIngredientAmountSerializer(
        many=True, source='recipe'
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return user.favorite_recipe.filter(recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return user.shopping_cart.filter(recipe=obj).exists()
        return False


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Write Serializer for RecipeViewSet."""
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    ingredients = IngredientAmountSerializer(
        many=True
    )
    image = Base64ImageField(
        max_length=None,
        use_url=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time',  
        )
        read_only_fields = ('id', 'author')

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)

        for ingredient in ingredients:
            ingredient_id, amount = ingredient['id'], ingredient['amount']
            RecipeIngredientAmount.objects.create(
                recipe=recipe,
                ingredient_id=ingredient_id,
                amount=amount
            )
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.save()

        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            instance.ingredients.clear()
        
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            instance.tags.clear()

        for ingredient in ingredients:
            ingredient_id, amount = ingredient['id'], ingredient['amount']
            RecipeIngredientAmount.objects.create(
                recipe=instance,
                ingredient_id=ingredient_id,
                amount=amount
            )
        instance.tags.set(tags)
        return instance

    def to_representation(self, instance):
        serializer = RecipeReadSerializer(
            instance,
            context={
                'request': self.context['request']
            }
        )
        return serializer.data

    def validate(self, data):
        recipe_name, recipe_text = data['name'], data['text']
        recipe = Recipe.objects.filter(
            name=recipe_name, text=recipe_text).exists()
        if recipe:
            raise serializers.ValidationError(
                f'Данный рецепт "{recipe_name}" уже существует.'
            )
        ingredients = data['ingredients']
        return data

    def validate_ingredients(self, value):
        ingredients_in_recipe = []
        if not value:
            raise serializers.ValidationError(
                'Рецепт не может быть без ингредиентов.'
            )
        for ingredient in value:
            ingredient_obj = get_object_or_404(
                Ingredient, pk=ingredient['id'] 
            )
            if ingredient_obj in ingredients_in_recipe:
                raise serializers.ValidationError(
                    'Рецепт не может иметь двух одиноковых ингредиентов.'
                )
            ingredients_in_recipe.append(ingredient_obj)
            if ingredient['amount'] < 0:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть больше 0.'
                )
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Рецепт должен иметь хотя бы 1 тэг.'
            )
        for tag in value:
            if not Tag.objects.filter(name=tag).exists():
                raise serializers.ValidationError(
                    f'Данного тэга {tag} нет в списке доступных.'
                )
        return value

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Время приготовления должно быть больше 1 мин.'
            )
        return value


class ShortRecipeSerializer(serializers.ModelSerializer):
    """
    Serializes a short variant of recipe.
    Uses in SubscriptionSerializer.
    """
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for Subscription.
    """
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.BooleanField(read_only=True)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        """
        Method field.
        Method returns list of the author's recipes.
        Provides the recipe limitation to return.
        """
        request = self.context['request']
        recipe_limit = request.GET.get('recipes_limit')
        if recipe_limit:
            recipes = obj.author.recipe.all()[:int(recipe_limit)] 
        else:
            recipes = obj.author.recipe.all()
        serializer = ShortRecipeSerializer(
            recipes, many=True, context={'request': request}
        )
        return serializer.data

    def get_recipes_count(self, obj):
        """
        Method field.
        Method returns the count of the author's recipes.
        """
        results = Recipe.objects.filter(author=obj.author).aggregate(
            count_recipes=Count('name')
        )
        return results['count_recipes']
