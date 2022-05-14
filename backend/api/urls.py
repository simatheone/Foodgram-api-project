from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from .views import (CustomUserViewSet, FavoriteAPIView, IngredientViewSet,
                    RecipeViewSet, ShoppingCartAPIView, SubscribeAPIView,
                    TagViewSet)

app_name = 'api'

router_v1 = DefaultRouter()
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')
router_v1.register('recipes', RecipeViewSet, basename='recipe')
router_v1.register('users', CustomUserViewSet, basename='users')


urlpatterns = [
    path('', include(router_v1.urls)),
    path('users/<int:user_id>/subscribe/',
         SubscribeAPIView.as_view(),
         name='subscribe'
         ),
    path('recipes/<int:recipe_id>/favorite/',
         FavoriteAPIView.as_view(),
         name='favorite'
         ),
    path('recipes/<int:recipe_id>/shopping_cart/',
         ShoppingCartAPIView.as_view(),
         name='shopping_cart'
         ),
    re_path(r'auth/', include('djoser.urls.authtoken'))
]
