import subscribe as subscribe
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from djoser.views import UserViewSet

from recipes.models import (Recipe, IngredientInRecipe, Ingredient,
                            Tag, Favorite, ShoppingList)
from users.models import User, Follow

from .pagination import CustomPagination
from .permissions import IsAuthorOrReadOnly, IsAdminOrReadOnly
from .serializers import (TagSerializer, IngredientSerializer,
                          RecipeSerializer, UserSerializer,
                          FollowSerializer, ShortRecipeSerializer,)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Tags"""

    permission_classes = (IsAdminOrReadOnly,)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Ingredients"""

    permission_classes = (IsAdminOrReadOnly,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet for Recipes"""

    permission_classes = (IsAuthorOrReadOnly,)
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def add_obj(self, model: object, user, pk):
        if model.objects.filter(user=user, recipe__id=pk).exists:
            return Response({
                'error': 'Recipe is already added to the list'
            }, status=status.HTTP_400_BAD_REQUEST)
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = ShortRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_obj(self, model: object, user, pk):
        obj = model.objects.filter(user=user, recipe__id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk):
        if request.method == 'GET':
            return add_obj(Favorite, request.user, pk)
        elif request.method == 'DELETE':
            return delete_obj(Favorite, request.user, pk)

    @action(detail=True, permission_classes=(IsAuthenticated,))
    def shopping_list(self, request, pk):
        if request.method == 'GET':
            return add_obj(ShoppingList, request.user, pk)
        elif request.method == 'DELETE':
            return delete_obj(ShoppingList, request.user, pk)

    #@action(detail=False, permission_classes=(IsAuthenticated,))
    #def download_shopping_cart(self, request):


class UsersViewSet(UserViewSet):
    """ViewSet for Users"""

    pagination_class = CustomPagination

    @action(detail=True, permission_classes=(IsAuthenticated,))
    def follow(self, request, id):
        user = request.user
        author = get_object_or_404(User, id=id)
        following = Follow.objects.create(user=user, author=author)
        serializer = FollowSerializer(following, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_following(self, request, id):
        user = request.user
        author = get_object_or_404(User, id=id)
        follow = Follow.objects.filter(user=user, author=author)
        if follow.exists():
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'you have already unfollowed'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def show_followings(self, request):
        user = request.user
        queryset = Follow.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
