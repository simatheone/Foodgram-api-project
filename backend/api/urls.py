from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter

from .views import (
    TagViewSet, IngredientViewSet, RecipeViewSet, CustomUserViewSet,
    FavoriteViewSet, ShoppingCartViewSet, SubscribeAPIView
)

app_name = 'api'

router_v1 = DefaultRouter()
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')
router_v1.register('recipes', RecipeViewSet, basename='recipe')
router_v1.register('users', CustomUserViewSet, basename='users')
router_v1.register(
    r'recipes/(?P<recipe_id>\d+)/favorite',
    FavoriteViewSet,
    basename='favorite'
)
router_v1.register(
    r'recipes/(?P<recipe_id>\d+)/shopping_cart',
    ShoppingCartViewSet,
    basename='shopping_cart'
)
# router_v1.register(
#     r'users/(?P<user_id>\d+)/subscribe/',
#     SubscribeViewSet,
#     basename='subscribe'
# )

urlpatterns = [
    path('', include(router_v1.urls)),
    path('users/<int:user_id>/subscribe/',
           SubscribeAPIView.as_view(), name='subscribe' ),
    re_path(r'auth/', include('djoser.urls.authtoken'))
]
