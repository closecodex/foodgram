import base64

from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.response import Response

from api.models import (
    Ingredient, IngredientInRecipe, Recipe, Subscription, Tag
)
from users.models import User

MIN_VALUE = 1
MAX_VALUE = 32000


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователя."""

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'password'
        )
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        """Создание нового пользователя."""

        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения информации о пользователе."""

    avatar = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name',
            'last_name', 'avatar', 'password', 'is_subscribed'
        )
        extra_kwargs = {'password': {'write_only': True}}

    def get_avatar(self, obj):
        """Получает URL аватара пользователя."""

        request = self.context['request']
        if obj.avatar:
            return request.build_absolute_uri(obj.avatar.url)
        return ''

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на другого."""

        request = self.context['request']
        user = request.user
        if not user.is_anonymous:
            return user.subscriptions.filter(author=obj).exists()
        return False


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения ингредиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField(
        min_value=MIN_VALUE,
        max_value=MAX_VALUE
    )

    class Meta:
        model = IngredientInRecipe
        fields = ['id', 'name', 'measurement_unit', 'amount']


class Base64ImageField(serializers.ImageField):
    """Поле для обработки изображений, закодированных в base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class AvatarSerializer(UserSerializer):
    """Сериализатор для обработки аватаров пользователей."""

    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'avatar',
        )

    def validate(self, attrs):
        """Проверяет наличие аватара в данных."""
        if 'avatar' not in attrs:
            raise serializers.ValidationError(
                {'avatar': 'Аватар не был передан.'}
            )
        return attrs


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения тегов рецептов."""

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецептов."""

    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        many=True, source='ingredientinrecipe_set'
    )
    tags = TagSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'author', 'name', 'image', 'text',
            'ingredients', 'tags', 'is_favorited',
            'is_in_shopping_cart', 'cooking_time'
        ]

    def get_image(self, obj):
        """Возвращает URL изображения рецепта."""

        request = self.context['request']
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return ''

    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное текущим пользователем."""

        user = self.context['request'].user
        if user.is_authenticated:
            return obj.favorited_by.filter(user=user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, добавлен ли рецепт в корзину текущим пользователем."""

        user = self.context['request'].user
        if user.is_authenticated:
            return user.shopping_cart.filter(recipe=obj).exists()
        return False


class IngredientWriteSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        min_value=MIN_VALUE,
        max_value=MAX_VALUE
    )

    def validate_amount(self, value):
        if value < MIN_VALUE:
            raise serializers.ValidationError(
                'Количество должно быть больше 0.'
            )
        return value


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и редактирования рецептов."""

    ingredients = IngredientWriteSerializer(
        many=True,
        write_only=True
    )
    tags = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all()),
        write_only=True,
        required=True
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        min_value=MIN_VALUE,
        max_value=MAX_VALUE
    )

    class Meta:
        model = Recipe
        fields = [
            'id', 'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time'
        ]

    def validate_ingredients(self, value):
        """Проверяет правильность данных ингредиентов."""

        if not value:
            raise serializers.ValidationError(
                'Необходимо добавить хотя бы один ингредиент.'
            )

        ingredients_set = set()
        for ingredient_data in value:
            ingredient = ingredient_data['id']
            if ingredient in ingredients_set:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться.'
                )
            ingredients_set.add(ingredient)
        return value

    def validate(self, data):
        """Валидация данных рецепта."""

        if 'ingredients' not in data:
            raise serializers.ValidationError(
                {'ingredients': 'Это поле обязательно.'}
            )
        if 'tags' not in data:
            raise serializers.ValidationError(
                {'tags': 'Это поле обязательно.'}
            )
        return data

    def validate_tags(self, value):
        """Валидация тегов."""

        if not value:
            raise serializers.ValidationError(
                'Необходимо добавить хотя бы один тег.'
            )
        if len(set(value)) != len(value):
            raise serializers.ValidationError('Теги не должны повторяться.')
        return value

    def create_ingredients(self, recipe, ingredients_data):
        """Создание объектов ингредиентов для рецепта."""
        ingredients_list = []
        for ingredient_data in ingredients_data:
            ingredient = ingredient_data['id']
            amount = ingredient_data['amount']
            ingredients_list.append(
                IngredientInRecipe(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=amount
                )
            )
        IngredientInRecipe.objects.bulk_create(ingredients_list)

    def create(self, validated_data):
        """Создание нового рецепта."""
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        self.create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        """Обновление существующего рецепта."""
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags_data is not None:
            instance.tags.set(tags_data)

        if ingredients_data is not None:
            instance.ingredients.clear()
            self.create_ingredients(instance, ingredients_data)

        return instance

    def partial_update(self, request, *args, **kwargs):
        """
        Частичное обновление объекта.
        """
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class RecipeShortSerializer(serializers.ModelSerializer):
    """Краткий сериализатор рецептов."""

    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        """Возвращает URL изображения рецепта."""
        request = self.context['request']
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return ''


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения подписок пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count', read_only=True
    )

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name',
            'last_name', 'avatar', 'is_subscribed',
            'recipes', 'recipes_count'
        ]

    def get_is_subscribed(self, obj):
        """
        Проверяет, подписан ли текущий пользователь на
        другого пользователя.
        """
        request = self.context['request']
        user = request.user
        if not user.is_anonymous:
            return user.subscriptions.filter(author=obj).exists()
        return False

    def get_recipes(self, obj):
        """Возвращает рецепты автора."""
        request = self.context['request']
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        serializer = SimpleRecipeSerializer(
            recipes, many=True, context={'request': request}
        )
        return serializer.data

    def get_avatar(self, obj):
        """Возвращает URL аватара пользователя."""
        request = self.context['request']
        if obj.avatar:
            return request.build_absolute_uri(obj.avatar.url)
        return ''


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['user', 'author']
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=['user', 'author'],
                message='Вы уже подписаны на этого пользователя.'
            )
        ]

    def validate(self, data):
        user = data['user']
        author = data['author']
        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.'
            )
        return data


class SimpleRecipeSerializer(serializers.ModelSerializer):
    """Простой сериализатор для рецептов (в подписках и избранном)."""

    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']

    def get_image(self, obj):
        """Возвращает URL изображения рецепта."""
        request = self.context['request']
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return ''


class SetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Неверный текущий пароль.')
        return value
