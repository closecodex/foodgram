from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CustomUserViewSet
from api.views import IngredientViewSet, RecipeViewSet, TagViewSet

api_v1 = DefaultRouter()
api_v1.register(r'users', CustomUserViewSet, basename='users')
api_v1.register(r'tags', TagViewSet, basename='tags')
api_v1.register(r'recipes', RecipeViewSet, basename='recipes')
api_v1.register(r'ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('', include(api_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
