from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import CustomUser, Subscription
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAdminOrReadOnly, IsOwnerAdminOrReadOnly
from .serializers import (CustomUserSerializer, IngredientSerializer,
                          RecipeReadSerializer, RecipeWriteSerializer,
                          ShortRecipeSerializer, SubscriptionSerializer,
                          TagSerializer)
from .utils import create_pdf_shopping_cart

SELF_FOLLOWING_ERROR = 'Пользователь не может подписаться сам на себя.'
DOUBLE_FOLLOWING_ERROR = 'Нельзя дважды подписаться на одного юзера.'
DOUBLE_FAVORITE_ERROR = 'Нельзя дважды добавить рецепт в избранное.'
DOUBLE_SHOPPING_ERROR = 'Нельзя добавить в покупки два одинаковых рецепта.'


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    The viewset for Tag model.
    Allowed request methods: GET.
    Permissions: All users.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)


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
    serializer_class = CustomUserSerializer

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
        serializer = SubscriptionSerializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubscribeAPIView(generics.ListCreateAPIView,
                       generics.DestroyAPIView):
    """
    APIView for Subscription model.
    Allowed request methods: POST, DELETE.
    Permissions: Authenticated users.
    """
    serializer_class = SubscriptionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        author_id = self.kwargs['user_id']
        queryset = get_object_or_404(CustomUser, pk=author_id)
        return queryset

    def create(self, request, *args, **kwargs):
        user = request.user
        author_obj = self.get_queryset()
        if user == author_obj:
            return Response(
                {'message': SELF_FOLLOWING_ERROR},
                status=status.HTTP_400_BAD_REQUEST
            )
        if user.sub_user.filter(author=author_obj).exists():
            return Response(
                {'message': DOUBLE_FOLLOWING_ERROR},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription = Subscription.objects.create(
            user=user, author=author_obj
        )
        serializer = self.get_serializer(
            subscription, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, user_id=None):
        user = self.request.user
        author = get_object_or_404(CustomUser, pk=user_id)
        subscription = Subscription.objects.filter(author=author, user=user)
        if not subscription:
            return Response(status=status.HTTP_400_BAD_REQUEST)
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
        create_pdf_shopping_cart(user)


class FavoriteAPIView(generics.CreateAPIView,
                      generics.DestroyAPIView):
    """
    ApiView for Favorite model.
    Allowed request methods: POST, DELETE.
    Permissions: Authenticated users.
    """
    serializer_class = ShortRecipeSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        recipe_id = self.kwargs['recipe_id']
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        self.check_object_permissions(self.request, recipe)
        return recipe

    def post(self, request, *args, **kwargs):
        recipe_obj = self.get_queryset()
        user = request.user
        if Favorite.objects.filter(user=user, recipe=recipe_obj).exists():
            return Response(
                {'message': DOUBLE_FAVORITE_ERROR},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(
            recipe_obj, context={'request': request}
        )
        Favorite.objects.create(user=user, recipe=recipe_obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        user = request.user
        recipe_obj = self.get_queryset()
        favorite = Favorite.objects.filter(user=user, recipe=recipe_obj)
        if not favorite:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartAPIView(generics.CreateAPIView,
                          generics.DestroyAPIView):
    """
    APIView for ShoppingCart model.
    Allowed request methods: POST, DELETE.
    Permissions: Authenticated users.
    """
    serializer_class = ShortRecipeSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        recipe_id = self.kwargs['recipe_id']
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        self.check_object_permissions(self.request, recipe)
        return recipe

    def post(self, request, *args, **kwargs):
        recipe_obj = self.get_queryset()
        user = request.user
        if ShoppingCart.objects.filter(user=user, recipe=recipe_obj).exists():
            return Response(
                {'message': DOUBLE_SHOPPING_ERROR},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(recipe_obj)
        ShoppingCart.objects.create(user=user, recipe=recipe_obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        user = request.user
        recipe_obj = self.get_queryset()
        shopping_cart = Favorite.objects.filter(user=user, recipe=recipe_obj)
        if not shopping_cart:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        shopping_cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
