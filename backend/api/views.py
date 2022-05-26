from django.contrib.auth.hashers import make_password
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from foodgram.settings import SHOPPING_CART_FILENAME
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import CustomUser, Subscription
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAdminOrReadOnly, IsOwnerAdminOrReadOnly
from .serializers import (CustomUserReadSerializer,
                          CustomUserSetPasswordSerializer,
                          CustomUserWriteSerializer, IngredientSerializer,
                          RecipeReadSerializer, RecipeWriteSerializer,
                          ShortRecipeSerializer, SubscriptionSerializer,
                          TagSerializer)
from .utils import create_pdf_shopping_cart

CART_DELETION_ERROR = 'Рецепт уже удален из списка покупок.'
DELETION_ERROR = 'Рецепт уже удален из списка.'
DOUBLE_ADD_ERROR = 'Рецепт нельзя добавить дважды.'
DELETE_SUB_ERROR = 'Подписка уже удалена либо не была ранее создана.'
DOUBLE_FOLLOWING_ERROR = 'Нельзя дважды подписаться на одного юзера.'
SELF_FOLLOWING_ERROR = 'Пользователь не может подписаться сам на себя.'


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    The viewset for Tag model.
    Allowed request methods: GET.
    Permissions: All users.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    The viewset for Ingredient model.
    Allowed request methods: GET.
    Permissions: All users.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None


class CustomUserViewSet(UserViewSet):
    """
    The viewset for model CustomUser.
    The viewset inherits from UserViewSet for Djoser library.
    Available endpoints with:
        GET method:
            api/users/, api/users/{user_id}/,
            api/users/me/, api/users/subscriptions/
        POST method:
            api/users/, api/users/set_password/,
            api/auth/token/login/, api/auth/token/logout/
    Permissions are set in Djoser library.
    """
    queryset = CustomUser.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CustomUserReadSerializer
        return CustomUserWriteSerializer

    def perform_create(self, serializer):
        if 'password' in self.request.data:
            password = make_password(self.request.data['password'])
            serializer.save(password=password)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=(IsAuthenticated,),
        url_name='set_password'
    )
    def set_password(self, request):
        """
        Additional method for the endpoint: api/users/set_password.
        Allowed request methods: POST.
        Permissions: Authenticated user.
        """
        serializer = CustomUserSetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                {'message': 'Пароль успешно изменен'},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_name='subscriptions'
    )
    def subscriptions(self, request):
        """
        Additional method for the endpoint: api/users/subscriptions.
        Allowed request methods: GET.
        Permissions: Authenticated user.
        """
        user = self.request.user
        queryset = user.sub_user.all()
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_name='subscribe'
    )
    def subscribe(self, request, id):
        """
        Additional method for the endpoint:
            api/users/<user_id>/subscribe/
        Allowed request methods: POST, DELETE.
        Permissions: Authenticated users.
        """
        user = request.user
        author = get_object_or_404(CustomUser, pk=id)
        subscription = user.sub_user.filter(author=author)
        if request.method == 'POST':
            if user == author:
                return Response(
                    {'message': SELF_FOLLOWING_ERROR},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if subscription.exists():
                return Response(
                    {'message': DOUBLE_FOLLOWING_ERROR},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = SubscriptionSerializer(
                author, context={'request': request}
            )
            Subscription.objects.create(user=user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not subscription:
                return Response(
                    {'message': DELETE_SUB_ERROR},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    """
    The viewset for Recipe model.
    Allowed request methods: GET, POST, PATCH, DELETE.
    Permissions:
        - All users can get a list of recipes;
        - Authenticated users can create/patch/delete recipes;
        - Only the owner of the recipe can patch/delete it.
    Filtering:
        - by authors id's;
        - by tags' slug;
        - by in_favorited (1 or 0);
        - by in_shopping_cart (1 or 0);
    """
    queryset = Recipe.objects.all()
    permission_classes = (IsOwnerAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    def favorite_or_shopping_cart(self, model, pk, request):
        """
        Method which creates/deletes object depends on model
        has been given to it.
        Works with models: Favorite, ShoppingCart.
        """
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        queryset = model.objects.filter(user=user, recipe=recipe)
        if request.method == 'POST':
            if queryset.exists():
                return Response(
                    {'message': DOUBLE_ADD_ERROR},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = ShortRecipeSerializer(
                recipe,
                context={'request': request}
            )
            model.objects.create(user=user, recipe=recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not queryset:
                return Response(
                    {'message': DELETION_ERROR},
                    status=status.HTTP_400_BAD_REQUEST
                )
            queryset.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_name='download_recipe'
    )
    def download_shopping_cart(self, request):
        """
        Additional method for the endpoint: api/recipes/download_shopping_cart.
        Returns PDF file for downloading with Ingredients.
        Allowed request methods: GET.
        Permissions: Authenticated user.
        """
        user = request.user
        buffer = create_pdf_shopping_cart(user)
        filename = f'{user.username}\'s-{SHOPPING_CART_FILENAME}'
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=filename
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_name='favorite'
    )
    def favorite(self, request, pk):
        """
        Additional method for the endpoint:
            api/recipes/<recipe_id>/favorite/
        Allowed request methods: POST, DELETE.
        Permissions: Authenticated users.
        """
        model = Favorite
        return self.favorite_or_shopping_cart(
            model, pk, request
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_name='shopping_cart'
    )
    def shopping_cart(self, request, pk):
        """
        Additional method for the endpoint:
            api/recipes/<recipe_id>/shopping_cart/
        Allowed request methods: POST, DELETE.
        Permissions: Authenticated users.
        """
        model = ShoppingCart
        return self.favorite_or_shopping_cart(
            model, pk, request
        )
