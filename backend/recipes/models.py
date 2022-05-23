from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core import validators
from django.db import models
from django.db.models import UniqueConstraint

from foodgram.settings import MAX_LEN_REPR

CustomUser = get_user_model()

MIN_AMOUNT_MESSAGE = 'Количество ингредиента должно быть больше 0.'


class Tag(models.Model):
    """Tag model."""
    name = models.CharField(
        'Название',
        max_length=200,
        unique=True
    )
    color = ColorField(
        verbose_name='Цвет',
        max_length=7,
        unique=True,
        default='#F29C1B'
    )
    slug = models.SlugField(
        'Слаг',
        unique=True
    )

    class Meta:
        db_table = 'tag'
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        indexes = [
            models.Index(
                fields=('name',), name='tag_name_idx'
            )
        ]

    def __str__(self):
        return self.name[:MAX_LEN_REPR]


class Ingredient(models.Model):
    """Ingredient model."""
    name = models.CharField(
        'Ингридиент',
        max_length=200
    )
    measurement_unit = models.CharField(
        'Единицы измерения',
        max_length=200
    )

    class Meta:
        db_table = 'ingredient'
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        indexes = [
            models.Index(
                fields=('name',), name='ingredient_name_idx'
            )
        ]
        constraints = [
            UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_name_with_measurement_unit'
            ),
        ]

    def __str__(self):
        return self.name[:MAX_LEN_REPR]


class RecipeIngredientAmount(models.Model):
    """
    Model RecipeIngredientAmount.
    Connects with Ingredient model.
    """
    ingredient = models.ForeignKey(
        Ingredient,
        related_name='ingredient',
        on_delete=models.CASCADE,
        verbose_name='Игредиент'
    )
    recipe = models.ForeignKey(
        'Recipe',
        related_name='recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    amount = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='Количество',
        validators=(
            validators.MinValueValidator(
                1, message=MIN_AMOUNT_MESSAGE
            ),
        )
    )

    class Meta:
        db_table = 'ingredient_amount_recipe'
        verbose_name = 'Ингредиент количество'
        verbose_name_plural = 'Ингредиенты количество'
        constraints = [
            UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_ingredient_for_recipe')
        ]

    def __str__(self):
        return str(self.amount)


class Recipe(models.Model):
    """Recipe model."""
    author = models.ForeignKey(
        CustomUser,
        related_name='recipe',
        on_delete=models.SET_NULL,
        null=True
    )
    name = models.CharField(
        'Название рецепта',
        max_length=200,
    )
    image = models.ImageField(
        'Картинка блюда',
        upload_to='recipes/images/',
    )
    text = models.TextField(
        'Текстовое описание рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name='recipes',
        through='RecipeIngredientAmount',
        verbose_name='Ингредиент'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Тэг'
    )
    cooking_time = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='Время приготовления'
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    class Meta:
        db_table = 'recipe'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)
        indexes = [
            models.Index(
                fields=('name',), name='recipe_name_idx'
            ),
            models.Index(
                fields=('author',), name='recipe_author_idx'
            )
        ]

    def __str__(self):
        return self.name[:MAX_LEN_REPR]


class Favorite(models.Model):
    """
    Favorite model.
    Chained models: User, Recipe
    """
    user = models.ForeignKey(
        CustomUser,
        related_name='favorite_recipe',
        on_delete=models.CASCADE,
        verbose_name='Юзер'
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='favorite_recipe',
        on_delete=models.CASCADE,
        verbose_name='Понравившийся рецепт'
    )

    class Meta:
        db_table = 'favorite'
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'

    def __str__(self):
        return f'{self.user} добавил(-а) в избранное {self.recipe}'


class ShoppingCart(models.Model):
    """
    Shopping Cart model.
    Chained models: User, Recipe
    """
    user = models.ForeignKey(
        CustomUser,
        related_name='shopping_cart',
        on_delete=models.CASCADE,
        verbose_name='Юзер'
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='shopping_cart',
        on_delete=models.CASCADE,
        verbose_name='Рецепты для покупок'
    )

    class Meta:
        db_table = 'shopping_cart'
        verbose_name = 'Список покупок'

    def __str__(self):
        return f'{self.user} добавил(-а) в покупки рецепт: {self.recipe}'
