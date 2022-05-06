from django.http import FileResponse
from djoser.views import UserViewSet
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework import viewsets, views, status
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination

from recipes.models import Ingredient, Tag, Recipe, Favorite, ShoppingCart
from users.models import CustomUser, Subscription
from .serializers import (
    CustomUserSerializer, IngredientSerializer, TagSerializer,
    RecipeSerializer, FavoriteSerializer, RecipeSerializer,
    ShoppingCartSerializer, SubscriptionSerializer
)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """TagViewSet for listing and retrieving Tags."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """IngredientViewSet for listing and retrieving Ingredients."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('^name',)


# ВНИМАНИЕ!!! ТУТ ПОМЕНЯЛ НАСЛЕДОВАНИ ОТ КЛАСАА ReadOnlyModelViewSet
# ПРОВЕРИТЬ ПРАВИЛЬНОСТЬ РАБОТЫ
class CustomUserViewSet(UserViewSet):
    """
    The viewset for model CustomUser.
    Available endpoints with get method: 
    api/users/, api/users/{user-id}/, api/users/me/
    """
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        if self.action in ('subscriptions', 'subscribe'):
            queryset = Subscription.objects.filter(
                user=self.request.user
            )
            return queryset
        return super().get_queryset()
    
    def get_serializer_class(self):
        if self.action in ('subscriptions', 'subscribe'):
            return SubscriptionSerializer
        return super().get_serializer_class()

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_name='subscriptions'
    )
    def subscriptions(self, request):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        print(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_name='subscribe'
    )
    def subscribe(self, request, id):
        author = get_object_or_404(CustomUser, pk=id)
        user = request.user
        if request.method == 'POST':
            instance = Subscription(user=user, author=author)
            serializer = self.get_serializer(author=author, data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                print('SERIALIZER DATA!!!!')
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            subscription = get_object_or_404(Subscription, user=user, author=author)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RecipeSerializer
    # ADD lookup_field

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_name='recipe-favorite'
    )
    def favorite(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            request.data['user'] = user.id
            request.data['recipe'] = pk
            serializer = FavoriteSerializer(
                data=request.data, context={'request': request}
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            favorite_recipe = get_object_or_404(
                Favorite, recipe=recipe, user=user
            )
            favorite_recipe.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_name='download_recipe'
    )
    def download_shopping_cart(self, request):
        username = request.user.username
        queryset = ShoppingCart.objects.filter(user=request.user)
        buffer = io.BytesIO()
        x = canvas.Canvas(buffer)
        x.drawString(100, 100, 'Hello!')
        x.showPage()
        x.save()
        buffer.seek(0)
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=f'{username}\'s-shopping-cart.pdf'
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_name='shopping_cart_recipe'
    )
    def shopping_cart(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            request.data['user'] = user.id
            request.data['recipe'] = pk
            serializer = ShoppingCartSerializer(
                data=request.data, context={'request': request}
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            shopping_cart_recipe = get_object_or_404(
                ShoppingCart, recipe=recipe, user=user
            )
            shopping_cart_recipe.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
