from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from users.models import User

MIN_VALUE = 1
MAX_VALUE = 32000


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        max_length=256,
        verbose_name='Название ингредиента'
    )
    measurement_unit = models.CharField(
        max_length=64,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']

    def __str__(self):
        return self.name


class Subscription(models.Model):
    """Модель подписки."""

    user = models.ForeignKey(
        User,
        related_name='subscriptions',
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    author = models.ForeignKey(
        User,
        related_name='subscribers',
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        unique_together = ('user', 'author')

    def __str__(self):
        return f'{self.user} подписан на {self.author}'


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField(
        max_length=32,
        unique=True,
        verbose_name='Название тега'
    )
    slug = models.SlugField(
        max_length=32,
        unique=True,
        verbose_name='Слаг тега'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта'
    )
    name = models.CharField(
        max_length=256,
        verbose_name='Название рецепта'
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        blank=True,
        null=True,
        verbose_name='Изображение рецепта'
    )
    text = models.TextField(
        verbose_name='Описание рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        related_name='recipes',
        verbose_name='Ингредиенты рецепта'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги рецепта'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(MIN_VALUE),
            MaxValueValidator(MAX_VALUE)
        ],
        verbose_name='Время приготовления (мин)'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    """Модель ингредиента в рецепте."""

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(MIN_VALUE),
            MaxValueValidator(MAX_VALUE)
        ],
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        unique_together = ('ingredient', 'recipe')

    def __str__(self):
        return f'{self.ingredient} в {self.recipe}'


class ShoppingCart(models.Model):
    """Модель списка покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f'Список покупок пользователя {self.user}'


class Favorite(models.Model):
    """Модель избранного."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в избранное'
