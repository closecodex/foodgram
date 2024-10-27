import base64

from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from requests import Response
from users.models import User
from api.models import (
    Ingredient, IngredientInRecipe, Tag, Recipe, 
    Subscription, ShoppingCart, Favorite
)

class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователя."""

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'password')
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
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'avatar', 'password', 'is_subscribed')
        extra_kwargs = {'password': {'write_only': True}}

    def get_avatar(self, obj):
        """Получает URL аватара пользователя."""

        request = self.context.get('request')
        if obj.avatar:
            return request.build_absolute_uri(obj.avatar.url)
        return ''
    
    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на другого."""

        request = self.context.get('request')
        if request and not request.user.is_anonymous:
            return Subscription.objects.filter(user=request.user, author=obj).exists()
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
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')
    amount = serializers.IntegerField()

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
                {'detail': 'Аватар не был передан.'}
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
    ingredients = IngredientInRecipeSerializer(many=True, source='ingredientinrecipe_set')
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

        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return ''
    
    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное текущим пользователем."""

        user = self.context.get('request').user
        if user.is_authenticated:
            return Favorite.objects.filter(user=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, добавлен ли рецепт в корзину текущим пользователем."""

        user = self.context.get('request').user
        if user.is_authenticated:
            return ShoppingCart.objects.filter(user=user, recipe=obj).exists()
        return False
    
class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и редактирования рецептов."""

    ingredients = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=True
    )
    tags = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all()),
        write_only=True,
        required=True
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time'
        ]

    def validate_ingredients(self, value):
        """Проверяет правильность данных ингредиентов."""

        if not value:
            raise serializers.ValidationError('Необходимо добавить хотя бы один ингредиент.')

        ingredients_set = set()
        for ingredient_data in value:
            ingredient_id = ingredient_data.get('id')
            amount = ingredient_data.get('amount')

            if ingredient_id is None:
                raise serializers.ValidationError('Отсутствует ID ингредиента.')
            if amount is None:
                raise serializers.ValidationError('Отсутствует количество ингредиента.')
            if int(amount) < 1:
                raise serializers.ValidationError('Количество ингредиента должно быть больше нуля.')
            if ingredient_id in ingredients_set:
                raise serializers.ValidationError('Ингредиенты не должны повторяться.')
            ingredients_set.add(ingredient_id)
            if not Ingredient.objects.filter(id=ingredient_id).exists():
                raise serializers.ValidationError(f"Ингредиент с ID {ingredient_id} не существует.")
        return value

    def validate(self, data):
        """Валидация данных рецепта."""

        if 'ingredients' not in data:
            raise serializers.ValidationError({'ingredients': 'Это поле обязательно.'})
        if 'tags' not in data:
            raise serializers.ValidationError({'tags': 'Это поле обязательно.'})
        return data

    def validate_tags(self, value):
        """Валидация тегов."""

        if not value:
            raise serializers.ValidationError('Необходимо добавить хотя бы один тег.')
        if len(set(value)) != len(value):
            raise serializers.ValidationError('Теги не должны повторяться.')
        return value
    
    def validate_image(self, value):
        """Валидация изображений."""

        if not value:
            raise serializers.ValidationError('Необходимо добавить изображение рецепта.')
        return value

    def validate_cooking_time(self, value):
        """Валидация время приготовления."""

        if value < 1:
            raise serializers.ValidationError('Время приготовления должно быть больше 0.')
        return value

    def create_ingredients(self, recipe, ingredients_data):
        """Создание объектов ингредиентов для рецепта."""

        ingredients_list = []
        for ingredient_data in ingredients_data:
            ingredient = get_object_or_404(Ingredient, id=ingredient_data['id'])
            ingredients_list.append(
                IngredientInRecipe(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=ingredient_data['amount']
                )
            )
        IngredientInRecipe.objects.bulk_create(ingredients_list)

    def create(self, validated_data):
        """Создание нового рецепта."""

        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        image = validated_data.pop('image')
        recipe = Recipe.objects.create(image=image, **validated_data)
        recipe.tags.set(tags_data)
        self.create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        """Обновление существующего рецепта."""

        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        image = validated_data.pop('image', instance.image)

        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time', instance.cooking_time)
        instance.image = image
        instance.save()

        instance.tags.clear()
        instance.tags.set(tags_data)

        instance.ingredients.clear()
        self.create_ingredients(instance, ingredients_data)

        return instance

    def partial_update(self, request, *args, **kwargs):
        """
        Частичное обновление объекта
        """
        
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
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

        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return ''


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения подписок пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'avatar', 'is_subscribed', 'recipes', 'recipes_count']

    def get_is_subscribed(self, obj):
        """
        Проверяет, подписан ли текущий пользователь на 
        другого пользователя.
        """

        request = self.context.get('request')
        if request and not request.user.is_anonymous:
            return Subscription.objects.filter(user=request.user, author=obj).exists()
        return False

    def get_recipes(self, obj):
        """Возвращает рецепты автора."""

        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        serializer = SimpleRecipeSerializer(recipes, many=True, context={'request': request})
        return serializer.data
    
    def get_avatar(self, obj):
        """Возвращает URL аватара пользователя."""

        request = self.context.get('request')
        if obj.avatar:
            return request.build_absolute_uri(obj.avatar.url)
        return ''
    
class SimpleRecipeSerializer(serializers.ModelSerializer):
    """Простой сериализатор для рецептов (в подписках и избранном)."""

    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']

    def get_image(self, obj):
        """Возвращает URL изображения рецепта."""

        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return ''