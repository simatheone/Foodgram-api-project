from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, TagViewSet

app_name = 'api'

router_v1 = DefaultRouter()
router_v1.register(r'tags', TagViewSet, basename='tags')
router_v1.register(r'ingredients', IngredientViewSet, basename='ingredients')


urlpatterns = [
    path('', include(router_v1.urls)),
    path(r'', include('djoser.urls')),
    path(r'^auth/', include('djoser.urls.authtoken'))
]



"""
AUTHORIZATION

/api/users/ - get (list of users)       perms: ALL
/api/users/ - post (registration of user)       perms: ALL

/api/users/{id}/ - get (user profile)       perms: Authenticated - TOKEN
/api/users/me/ - get (current user)       perms: Authenticated - TOKEN 

/api/users/set_password/ - post (password change)       perms: Authenticated
/api/auth/token/login/ - post (getting auth token)       perms: ALL
/api/auth/token/logout/ - post (deletion of a token)       perms: Authenticated
"""