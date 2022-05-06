from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import UniqueConstraint

from foodgram.settings import MAX_LEN_REPR


CustomUser = get_user_model()


class Tag(models.Model):
    """Tag model."""

    name = models.CharField(
        'Название',
        max_length=200,
        unique=True
    )
    color = models.CharField(
        'Цвет',
        max_length=7,
        unique=True
    )
    slug = models.SlugField(
        'Слаг',
        max_length=200,
        unique=True
    )

    class Meta:
        db_table = 'tag'
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        indexes = [
            models.Index(
                fields=['name'], name='tag_name_idx'
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
                fields=['name'], name='ingredient_name_idx'
            )
        ]
        constraints = [
            UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_name_with_measurement_unit'
            ),
        ]

    def __str__(self):
        return self.name[:MAX_LEN_REPR]


class IngredientAmount(models.Model):
    """
    Model IngredientAmount.
    Connects with Ingredient model.
    """

    ingredient = models.ForeignKey(
        Ingredient,
        related_name='ingredient_amount',
        on_delete=models.CASCADE
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество'
    )

    class Meta:
        db_table = 'ingredient_amount'
        verbose_name = 'Ингредиент-количество'
        verbose_name_plural = 'Ингредиенты-количества'

    def __str__(self):
        return str(self.amount)


class Recipe(models.Model):
    """Recipe model."""

    author = models.ForeignKey(
        CustomUser,
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
        related_name='recipe_ingredient',
        through='RecipeIngredient',
        verbose_name='Ингредиент'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipe_tag',
        through='RecipeTag',
        verbose_name='Тэг'
    )
    cooking_time = models.PositiveSmallIntegerField(
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
                fields=['name'], name='recipe_name_idx'
            ),
            models.Index(
                fields=['author'], name='recipe_author_idx'
            )
        ]

    def __str__(self):
        return self.name[:MAX_LEN_REPR]


class RecipeIngredient(models.Model):
    """
    Model though which the m2m relationship was established.
    Chained models: Recipe, Ingredient.
    """

    recipe = models.ForeignKey(
        Recipe,
        related_name='recipes',
        on_delete=models.SET_NULL,
        null=True
    )
    ingredient = models.ForeignKey(
        Ingredient,
        related_name='ingredients',
        on_delete=models.SET_NULL,
        null=True
    )

    class Meta:
        db_table='recipe_ingredient'
        verbose_name = 'Рецепт-ингредиент'
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'ingredient'], name='unique_ingredient_for_recipe'
            ),
        ]

    def __str__(self):
        return (f'В рецепт: {self.recipe}' 
               ' добавлен игредиент: {self.ingredient}')


class RecipeTag(models.Model):
    """
    Model though which the m2m relationship was established.
    Chained models: Recipe, Tag.
    """

    recipe = models.ForeignKey(
        Recipe,
        related_name='recipe',
        on_delete=models.SET_NULL,
        null=True
    )
    tag = models.ForeignKey(
        Tag,
        related_name='tag',
        null=True,
        on_delete=models.SET_NULL
    )

    class Meta:
        db_table='recipe_tag'
        verbose_name = 'Рецепт-тэг'
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'tag'], name='unique_tag_for_recipe'
            ),
        ]

    def __str__(self):
        return f'К рецепту: {self.recipe} добавлен тег: {self.tag}'


class Favorite(models.Model):
    """
    Favorite model.
    Chained models: User, Recipe
    """

    user = models.ForeignKey(
        CustomUser,
        related_name='favorite_user',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='favorite_recipe',
        on_delete=models.CASCADE
    )

    class Meta:
        db_table='favorite'
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'], name='unique_favorite_recipe'
            ),
        ]

    def __str__(self):
        return f'{self.user} добавил(-а) в избранное {self.recipe}'


class ShoppingCart(models.Model):
    """
    Shopping Cart model.
    Chained models: User, Recipe
    """

    user = models.ForeignKey(
        CustomUser,
        related_name='cart_user',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='cart_recipe',
        on_delete=models.CASCADE
    )

    class Meta:
        db_table='shopping_cart'
        verbose_name = 'Список покупок'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'], name='unique_recipe_for_user_in_the_cart'
            ),
        ]

    def __str__(self):
        return f'{self.user} добавил(-а) рецепт: {self.recipe}'
