from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, TagViewSet

app_name = 'api'

router_v1 = DefaultRouter()
router_v1.register(r'tags', TagViewSet, basename='tags')
router_v1.register(r'ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('', include(router_v1.urls)),
    re_path(r'', include('djoser.urls')),
    re_path(r'auth/', include('djoser.urls.authtoken'))
]
