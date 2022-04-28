from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework import viewsets, views, status, mixins
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination

from recipes.models import Ingredient, Tag
from users.models import CustomUser
from .serializers import (
    CustomUserSerializer, IngredientSerializer, TagSerializer
)


class ListRetrieveViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """
    Custom viewset for inheritance.
    Viewsets which inherits custom viewset: TagViewSet, IngredientViewSet.
    """
    pass


class TagViewSet(ListRetrieveViewSet):
    """
    TagViewSet for listing and retrieving Tags.
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(ListRetrieveViewSet):
    """
    IngredientViewSet for listing and retrieving Ingredients.
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('^name',)


class CustomUserViewSet(ListRetrieveViewSet):
    """
    The viewset for model CustomUser.
    Available endpoints with get method: 
    api/users/, api/users/{id}/, api/users/me/
    """

    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (AllowAny,)

    class Meta:
        model = CustomUser
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }
