from django.db import models
from django.contrib.auth import get_user_model


class Recipe(models.Model):
    """Recipe model."""

    author = models.ForeignKey(
        CusomUser,
        default='Deleted User',
        on_delete=models.SET_DEFAULT
    )
    name = models.CharField(
        'Название рецепта',
        max_length=256,
    )
    image = models.ImageField(
        'Картинка блюда',
        upload_to='recipes/images/',
    )
    text = models.TextField(
        'Текстовое описание рецепта'
    )
    ingredient = models.ManyToManyField(
        Ingredient,
        related_name='recipe_ingredient',
        through=RecipeIngredient,
        verbose_name='Ингредиент'
    )
    tag = models.ManyToManyFeld(
        Tag,
        related_name='recipe_tag',
        through=RecipeTag,
        verbose_name='Тэг'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления'
    )

    class Meta:
        db_table = 'recipe'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name[:30]


class RecipeIngredient(models.Model):
    """
    Model though which the m2m relationship was established.
    Chained models: Recipe, Ingredient.
    """

    recipe = models.ForeignKey(
        Recipe,
        related_name='recipe',
        on_delete=models.???
    )
    ingredient = models.ForeignKey(
        Ingredient,
        related_name='ingredient',
        on_delete=models.???
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
        on_delete=models.???
    )
    tag = models.ForeignKey(
        Tag,
        related_name='tag',
        on_delete=models.???
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

    def __str__(self):
        return self.name[:30]


class Ingredient(models.Model):
    """Ingredient model."""

    name = models.CharField(
        'Ингридиент',
        max_length=200
        )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество'
    )
    measurement_unit = models.CharField(
        'Единицы измерения',
        max_length=200
    )

    class Meta:
        db_table = 'ingredient'
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name[:30]


class Favorite(models.Model):
    """Favorite model."""

    user = models.ForeignKey(
        CustomUser,
        related_name='favorite_user',
        on_delete=models.???
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='favorite_recipe'
        on_delete=models.???
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


class Subscription(models.Model):
    """Subscription model."""

    user = models.ForeignKey(
        CusomUser,
        related_name='sub_user',
        on_delete=models.???
    )
    author = models.ForeignKey(
        CustomUser,
        related_name='sub_author',
        on_delete=models.???
    )

    class Meta:
        db_table='subscription'
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            UniqueConstraint(
                fields=['user', 'author'], name='unique_subscription'
            ),
            CheckConstraint(check=~Q(user=F('author')),
                            name='user_cant_follow_himself'),
        ]

    def __str__(self):
        return f'{self.user} подписался на {self.author}'


class ShoppingCart(models.Model):
    """
    Shopping Cart model.
    Chained models: User, Recipe
    """

    user = models.ForeignKey(
        User,
        related_name='cart_user',
        on_delete=models.???
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='cart_recipe',
        on_delete=models.???
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
