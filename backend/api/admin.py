from django.contrib import admin
from .models import (
    Ingredient, Subscription, Tag, Recipe,
    IngredientInRecipe, ShoppingCart, Favorite
)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка для модели ингредиента."""
    
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админка для модели тега."""

    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для модели рецепта."""

    list_display = ('name', 'author', 'cooking_time', 'created_at')
    search_fields = ('name', 'author__username')
    list_filter = ('tags', 'created_at')
    autocomplete_fields = ('author', 'ingredients', 'tags')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админка для модели подписок."""

    list_display = ('user', 'author')
    search_fields = ('user__username', 'author__username')
    list_filter = ('user', 'author')


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    """Админка для модели ингредиента в рецепте."""

    list_display = ('ingredient', 'recipe', 'amount')
    search_fields = ('ingredient__name', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админка для модели списка покупок."""

    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админка для модели избранного."""

    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
