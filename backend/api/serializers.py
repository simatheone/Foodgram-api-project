from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from django.db.models import Count
from django.shortcuts import get_object_or_404
from drf_base64.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import Ingredient, Recipe, RecipeIngredientAmount, Tag
from users.models import CustomUser, Subscription


class IsSubscribedMethod:
    """
    Class for inheritance.
    Uses in:
        CustomUserReadSerializer, CustomUserWriteSerializer,
        SubscriptionSerializer.
    Provides method get_is_subscribed which repeates in
    serializers that have been mentioned above.
    """
    def get_is_subscribed(self, obj):
        """
        Method checks if user is a subscriber of an author.
        """
        user = self.context['request'].user
        if user.is_authenticated:
            if isinstance(obj, CustomUser):
                return user.sub_user.filter(author=obj).exists()
            return True
        return False


class CustomUserReadSerializer(serializers.ModelSerializer,
                               IsSubscribedMethod):
    """
    Read Serializer for CustomUserViewset.
    Uses model: CustomUser.
    Serializes/deserializes fileds of a model:
    email, id, username, first_name, last_name and
    method field is_subscribed.
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


class CustomUserWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for CustomUserViewset.
    Uses model: CustomUser.
    Serializes/deserializes fileds of a model:
    email, id, username, first_name, last_name, password.
    """
    class Meta:
        model = CustomUser
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'password'
        )


class CustomUserSetPasswordSerializer(serializers.Serializer):
    """
    Serializer for action 'set_password', CustomUserViewset.
    Serializes/deserializes fileds:
    current_password, new_password.
    """
    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate_current_password(self, value):
        user = self.context['request'].user
        user_password = user.password

        if check_password(value, user_password) is False:
            raise serializers.ValidationError(
                'Неверно введен старый пароль.',
                code='authorization'
            )
        return value

    def validate_new_password(self, value):
        if not value:
            raise serializers.ValidationError(
                'Укажите "Новый пароль"'
            )
        validate_password(value)
        return value

    def create(self, validate_data):
        user = self.context['request'].user
        new_password = validate_data.get('new_password')
        user.set_password(new_password)
        user.save()
        return validate_data


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer for TagViewset.
    Uses model: Tag.
    Serializes/deserializes fileds of a model:
    id, name, color, slug.
    """
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """
    Serializer for IngredientViewSet.
    Uses model: Ingredient.
    Serializes/deserializes fileds of a model:
    id, name, measurement_unit.
    """
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientAmountSerializer(serializers.ModelSerializer):
    """
    Serializer is used in RecipeReadSerializer.
    Uses model: RecipeIngredientAmount.
    Serializes/deserializes fileds of Ingredient model:
    id, name, measurement_unit and additional 'amount' field.
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
    Serializer is used in RecipeWriteSerializer.
    Uses model: RecipeIngredientAmount.
    Serializes/deserializes fileds of a model:
    id, amount.
    """
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredientAmount
        fields = ('id', 'amount')

    def validate_amount(self, value):
        if value <= 0:
            return serializers.ValidationError(
                'Количество ингредиента должно быть больше 0.'
            )
        return value


class RecipeReadSerializer(serializers.ModelSerializer):
    """
    Read Serializer for RecipeViewset.
    Uses model: Recipe.
    Serializes/deserializes fileds of a model:
    id, tags, author, ingredients, name, image,
    text, cooking_time + additional method fields:
        is_favorited, is_in_shopping_cart.
    """
    author = CustomUserReadSerializer(
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
        """
        Method checks if user has recipe in favorite list.
        """
        user = self.context['request'].user
        if user.is_authenticated:
            return user.favorite_recipe.filter(recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        """
        Method checks if user has recipe in shopping cart.
        """
        user = self.context['request'].user
        if user.is_authenticated:
            return user.shopping_cart.filter(recipe=obj).exists()
        return False


class RecipeWriteSerializer(serializers.ModelSerializer):
    """
    Write Serializer for RecipeViewSet.
    Uses model: Recipe.
    Serializes/deserializes fileds of a model:
    id, tags, author, ingredients, name, image,
    text, cooking_time.
    """
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
            'name', 'image', 'text', 'cooking_time'
        )
        read_only_fields = ('id', 'author')

    def validate(self, data):
        recipe_name, recipe_text = data['name'], data['text']
        ingredient_amount = data['ingredients']
        if not ingredient_amount:
            raise serializers.ValidationError(
                'Рецепт не может быть создан без ингредиентов.'
            )
        list_of_ingredients = []
        for value in ingredient_amount:
            ingredient_obj = get_object_or_404(
                Ingredient, pk=value.get('id')
            )
            if ingredient_obj in list_of_ingredients:
                raise serializers.ValidationError(
                    'Рецепт не может иметь двух одиноковых ингредиентов.',
                )
            list_of_ingredients.append(ingredient_obj)

            amount = value['amount']
            if not isinstance(amount, int):
                error_message = amount.detail[0]
                raise serializers.ValidationError(
                    error_message
                )
        recipe = Recipe.objects.filter(
            name=recipe_name, text=recipe_text).exists()
        if recipe:
            raise serializers.ValidationError(
                f'Данный рецепт "{recipe_name}" уже существует.'
            )
        return data

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

            for ingredient in ingredients:
                ingredient_id, amount = ingredient['id'], ingredient['amount']
                RecipeIngredientAmount.objects.create(
                    recipe=instance,
                    ingredient_id=ingredient_id,
                    amount=amount
                )

        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            instance.tags.clear()
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


class ShortRecipeSerializer(serializers.ModelSerializer):
    """
    Serializes a short variant of recipe.
    Uses in SubscriptionSerializer.
    Uses model: Recipe.
    Serializes/deserializes fileds of Recipe model:
    id, name, image, cooking_time.
    """
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer,
                             IsSubscribedMethod):
    """
    Serializer for Subscription.
    Uses model: Subscription.
    Serializes/deserializes fileds of CustomUser:
    email, id, username, first_name, last_name
    + additional method fields:
        is_subscribed, recipes, recipes_count
    """
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField(
        read_only=True
    )
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        """
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
        Method returns the number of the author's recipes.
        """
        results = Recipe.objects.filter(author=obj.author).aggregate(
            count_recipes=Count('name')
        )
        return results['count_recipes']
