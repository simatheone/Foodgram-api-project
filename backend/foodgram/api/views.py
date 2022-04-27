from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework import viewsets, views, status, mixins
from rest_framework.response import Response
from rest_framework.filters import SearchFilter

from recipes.models import Ingredient, Tag
from .serializers import IngredientSerializer, TagSerializer



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
