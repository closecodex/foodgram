from django.db.models import Exists, OuterRef, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from users.models import User

from .filters import RecipeFilter
from .models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                     ShoppingCart, Subscription, Tag)
from .pagination import CustomPagination
from .permissions import IsAuthor
from .serializers import (AvatarSerializer, IngredientSerializer,
                          RecipeReadSerializer, RecipeShortSerializer,
                          RecipeWriteSerializer, SubscriptionSerializer,
                          TagSerializer, UserCreateSerializer, UserSerializer)


class CustomUserViewSet(UserViewSet):
    """
    Вьюсет для управления аккаунтами пользователей, создания новых
    пользователей, обновления аватаров и управления подписками.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination
    lookup_field = 'id'
    lookup_value_regex = '[0-9]+|me'

    def get_permissions(self):
        """
        Возвращает права доступа в зависимости от действия.
        """

        if self.action in ['create', 'list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        """
        Возвращает нужный сериализатор в зависимости от действия.
        """

        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        """
        Создает новый аккаунт пользователя.
        """

        serializer = self.get_serializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=False, methods=['PUT', 'PATCH', 'DELETE'],
            url_path='me/avatar', permission_classes=[IsAuthenticated])
    def update_avatar(self, request):
        """
        Обновляет или удаляет аватар пользователя.
        """

        user = request.user
        if request.method in ['PUT', 'PATCH']:
            serializer = AvatarSerializer(data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            avatar_data = serializer.validated_data.get('avatar')
            user.avatar = avatar_data
            user.save()
            image_url = request.build_absolute_uri(user.avatar.url)
            return Response(
                {'avatar': str(image_url)}, status=status.HTTP_200_OK
            )

        elif request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'],
            url_path='set_password', permission_classes=[IsAuthenticated])
    def set_password(self, request):
        """
        Изменяет пароль для текущего пользователя.
        """

        user = request.user
        new_password = request.data.get('new_password')
        current_password = request.data.get('current_password')
        if not user.check_password(current_password):
            return Response(
                {'current_password': ['Wrong password.']},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(new_password)
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            url_path='subscriptions', permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """
        Возвращает список авторов, на которых подписан пользователь.
        """

        user = request.user
        subscriptions = Subscription.objects.filter(user=user)
        authors = [sub.author for sub in subscriptions]

        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = SubscriptionSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(
            authors, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=['post'],
            url_path='subscribe', permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        """
        Подписка на автора.
        """

        user = request.user
        author = get_object_or_404(User, id=id)

        if user == author:
            return Response(
                {'errors': 'Нельзя подписаться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if Subscription.objects.filter(user=user, author=author).exists():
            return Response(
                {'errors': 'Вы уже подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        Subscription.objects.create(user=user, author=author)
        serializer = SubscriptionSerializer(
            author, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        """
        Отписка от автора.
        """

        user = request.user
        author = get_object_or_404(User, id=id)

        subscription = Subscription.objects.filter(
            user=user, author=author
        )
        if not subscription.exists():
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def retrieve(self, request, *args, **kwargs):
        """
        Возвращает данные о пользователе на основе ID,
        либо ошибку 404, если пользователь не найден.
        """
        try:
            user = self.get_object()
        except User.DoesNotExist:
            return Response(
                {'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.get_serializer(user)
        return Response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для просмотра тегов.
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    http_method_names = ['get']
    permission_classes = [AllowAny]
    pagination_class = None
    lookup_field = 'pk'


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Вьюсет для просмотра, создания, редактирования
    и удаления рецептов.
    """

    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    lookup_field = 'pk'

    def get_queryset(self):
        """
        'is_in_shopping_cart' фильтрует рецепты из корзины покупок;
        'is_favorited' фильтрует рецепты из избранного.
        """
        user = self.request.user
        queryset = Recipe.objects.all()

        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart'
        )
        if is_in_shopping_cart is not None and user.is_authenticated:
            queryset = queryset.annotate(
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=user, recipe=OuterRef('pk')
                    )
                )
            ).filter(
                is_in_shopping_cart=(
                    True if is_in_shopping_cart == '1' else False
                )
            )

        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited is not None and user.is_authenticated:
            queryset = queryset.annotate(
                is_favorite=Exists(
                    Favorite.objects.filter(user=user, recipe=OuterRef('pk'))
                )
            ).filter(is_favorite=True if is_favorited == '1' else False)

        return queryset

    def get_serializer_class(self):
        """
        Определяет использование сериализатора.
        """

        if self.action in ['list', 'retrieve']:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        """
        Сохраняет рецепт с текущим пользователем в качестве автора.
        """

        serializer.save(author=self.request.user)

    def get_permissions(self):
        """
        Определяет права доступа на основе действия.
        """

        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAuthor()]
        return [IsAuthenticatedOrReadOnly()]

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated], url_path='shopping_cart')
    def add_to_shopping_cart(self, request, pk=None):
        """
        Добавляет рецепт в корзину покупок.
        """

        user = request.user
        recipe = self.get_object()
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'errors': 'Рецепт уже в корзине покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )
        ShoppingCart.objects.create(user=user, recipe=recipe)
        serializer = RecipeShortSerializer(
            recipe, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @add_to_shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        """
        Удаляет рецепт из корзины покупок.
        """

        user = request.user
        recipe = self.get_object()
        shopping_cart_item = ShoppingCart.objects.filter(
            user=user, recipe=recipe
        )
        if not shopping_cart_item.exists():
            return Response(
                {'errors': 'Рецепта нет в корзине покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )
        shopping_cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated], url_path='favorite')
    def add_to_favorite(self, request, pk=None):
        """
        Добавляет рецепт в избранное пользователя.
        """

        user = request.user
        recipe = self.get_object()
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'errors': 'Рецепт уже в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Favorite.objects.create(user=user, recipe=recipe)
        serializer = RecipeShortSerializer(
            recipe, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @add_to_favorite.mapping.delete
    def remove_from_favorite(self, request, pk=None):
        """
        Удаляет рецепт из избранного пользователя.
        """

        user = request.user
        recipe = self.get_object()
        favorite_item = Favorite.objects.filter(user=user, recipe=recipe)
        if not favorite_item.exists():
            return Response(
                {'errors': 'Рецепта нет в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        favorite_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'],
            url_path='get-link', permission_classes=[AllowAny])
    def get_link(self, request, pk=None):
        """
        Возвращает короткую ссылку на рецепт.
        """

        recipe = self.get_object()
        data = {
            'short-link': f'http://89.169.173.241:8000/recipes/{recipe.id}/'
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated],
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        """
        Позволяет пользователю скачать список ингредиентов
        для всех рецептов в корзине покупок.
        """

        user = request.user
        ingredients = IngredientInRecipe.objects.filter(
            recipe__in=user.shopping_cart.values_list('recipe', flat=True)
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(amount_total=Sum('amount'))

        shopping_list = ''
        for item in ingredients:
            shopping_list += (
                f"{item['ingredient__name']} "
                f"({item['ingredient__measurement_unit']}) - "
                f"{item['amount_total']}\n"
            )

        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    def create(self, request, *args, **kwargs):
        """
        Создает новый рецепт с текущим пользователем в качестве автора.
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save(author=request.user)
        read_serializer = RecipeReadSerializer(
            recipe, context={'request': request}
        )
        headers = self.get_success_headers(read_serializer.data)
        return Response(
            read_serializer.data,
            status=status.HTTP_201_CREATED, headers=headers
        )

    def update(self, request, *args, **kwargs):
        """
        Обновляет данные о существующем рецепте.
        """

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()
        read_serializer = RecipeReadSerializer(
            recipe, context={'request': request}
        )
        return Response(read_serializer.data)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для просмотра ингредиентов.
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    http_method_names = ['get']
    pagination_class = None

    def get_queryset(self):
        """
        Возвращает отфильтрованный queryset ингредиентов.
        """

        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset
