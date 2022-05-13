import io

from django.http import FileResponse
from django.db.models import Value, Sum, Count, Exists
from djoser.views import UserViewSet
from django.shortcuts import get_object_or_404

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet

from rest_framework.decorators import action
from rest_framework import viewsets, views, status, mixins, generics
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from django_filters.rest_framework import DjangoFilterBackend

from foodgram.settings import SHOPPING_CART_FILENAME
from recipes.models import(
    Favorite, Ingredient, Recipe,
    RecipeIngredientAmount, ShoppingCart, Tag
)
from users.models import CustomUser, Subscription
from .serializers import (
    CustomUserSerializer, IngredientSerializer, TagSerializer,
    RecipeReadSerializer, RecipeWriteSerializer,
    SubscriptionSerializer, ShortRecipeSerializer
)
from .filters import RecipeFilter, IngredientFilter
from .permissions import IsAdminOrReadOnly, IsOwnerAdminOrReadOnly
from .utils import shopping_cart_dict

SELF_FOLLOWING_ERROR = 'Пользователь не может подписаться сам на себя.'
DOUBLE_FOLLOWING_ERROR = 'Нельзя дважды подписаться на одного юзера.'
DOUBLE_FAVORITE_ERROR = 'Нельзя дважды добавить рецепт в избранное.'

class CreateDestroyViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    pass


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """TagViewSet for listing and retrieving Tags."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """IngredientViewSet for listing and retrieving Ingredients."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_class = IngredientFilter
    permission_classes = (IsAdminOrReadOnly,)


class CustomUserViewSet(UserViewSet):
    """
    The viewset for model CustomUser.
    Available endpoints with: 
        GET method: 
            api/users/, api/users/{user_id}/,
            api/users/me/, api/users/subscriptions/
        POST method:
            api/users/, api/users/set_password/,
            api/auth/token/login/, api/auth/token/logout/
            api/users/{user_id}/subscribe/
        DELETE method:
            api/users/{user_id}/subscribe/
    """
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (AllowAny,) # от анонима пост запрос на регистрацию ????

    def get_queryset(self):
        user = self.request.user
        if self.action in ('subscriptions', 'subscribe'):
            queryset = user.sub_user.annotate(
                is_subscribed=Value(True)
            )
            return queryset
        return super().get_queryset()

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_name='subscriptions'
    )
    def subscriptions(self, request):
        user = request.user
        queryset = self.get_queryset()
        serializer = SubscriptionSerializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubscribeAPIView(generics.ListCreateAPIView,
                       generics.DestroyAPIView):
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
            message = 'Нельзя дважды подписаться на одного юзера.'
            return Response(
                {'message': DOUBLE_FOLLOWING_ERROR},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription = Subscription.objects.create(user=user, author=author_obj)
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
    queryset = Recipe.objects.all()
    permission_classes = (IsOwnerAdminOrReadOnly,)
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
        methods=['get'],
        permission_classes=(AllowAny,),
        url_name='download_recipe'
    )
    def download_shopping_cart(self, request):
        """
        PDF file for downloading with Ingredients.
        """
        user = request.user
        buffer = io.BytesIO()
        styles = getSampleStyleSheet()
        pdf_page = canvas.Canvas(buffer, pagesize=letter)

        # Set fonts for pdf file
        pdfmetrics.registerFont(TTFont('DejaVuSerif', 'DejaVuSerif.ttf', 'UTF-8'))
        pdf_page.setFont('DejaVuSerif', 16)

        # Set x and y positions for the text on the page
        # Set the indent size for the text
        x_value , y_value = 315, 735
        indent_size = 15

        recipes_list = user.shopping_cart.all()
        ingredients_list = shopping_cart_dict(recipes_list)

        if recipes_list:
            ingredients = []
            pdf_page.drawCentredString(315, 750, 'Список покупок')

            # for value in ingredients:
            #     pdf_page.drawString(
            #         x_value - indent_size, y_value, value
            #     )
            #     y_value -= 20
            pdf_page.save()
            buffer.seek(0)
            return FileResponse(
                buffer,
                as_attachment=True,
                filename=f'{user.username}\'s {SHOPPING_CART_FILENAME}'
            )
            

        pdf_page.drawCentredString(315, 425, 'Список покупок пуст')
        pdf_page.showPage()
        pdf_page.save()
        buffer.seek(0)
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=f'{user.username}\'s {SHOPPING_CART_FILENAME}'
        )

       

class FavoriteViewSet(CreateDestroyViewSet):
    serializer_class = ShortRecipeSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        recipe_id = self.kwargs['recipe_id']
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        self.check_object_permissions(self.request, recipe)
        return recipe

    def create(self, request, *args, **kwargs):
        recipe_obj = self.get_object()
        user = request.user
        if Favorite.objects.filter(user=user, recipe=recipe_obj).exists():
            return Response(
                {'message': DOUBLE_FAVORITE_ERROR},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(recipe_ob, context={'request': request})
        Favorite.objects.create(user=user, recipe=recipe_obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        user = request.user
        recipe_obj = self.get_object()
        favorite = Favorite.objects.filter(user=user, recipe=recipe_obj)
        if not favorite:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartViewSet(CreateDestroyViewSet):
    serializer_class = ShortRecipeSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        recipe_id = self.kwargs['recipe_id']
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        self.check_object_permissions(self.request, recipe)
        return recipe

    def create(self, request, *args, **kwargs):
        recipe_obj = self.get_object()
        user = request.user
        if ShoppingCart.objects.filter(user=user, recipe=recipe_obj).exists():
            message = 'Нельзя добавить в покупки два одинаковых рецепта.'
            return Response({'message': message}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(recipe_obj)
        ShoppingCart.objects.create(user=user, recipe=recipe_obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        user = request.user
        recipe_obj = self.get_object()
        shopping_cart = Favorite.objects.filter(user=user, recipe=recipe_obj)
        if not shopping_cart:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        shopping_cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
