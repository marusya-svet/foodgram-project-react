from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
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

    permission_classes = (AllowAny,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
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
            return self.add_obj(Favorite, request.user, pk)
        if request.method == 'DELETE':
            return self.delete_obj(Favorite, request.user, pk)

    @action(detail=True, permission_classes=(IsAuthenticated,))
    def shopping_list(self, request, pk):
        if request.method == 'GET':
            return self.add_obj(ShoppingList, request.user, pk)
        if request.method == 'DELETE':
            return self.delete_obj(ShoppingList, request.user, pk)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def download_shopping_list(self, request):
        shopping_list = {}
        ingredients = IngredientInRecipe.objects.filter(
            recipe__list__user=request.user).values_list(
            'ingredient__name', 'ingredient__measure_unit',
            'amount'
        )
        for ingredient in ingredients:
            name = ingredient[0]
            if name not in shopping_list:
                shopping_list[name] = {
                    'measure_unit': ingredient[1],
                    'amount': ingredient[2]
                }
            else:
                shopping_list[name]['amount'] += ingredient[2]
        response = HttpResponse(
            open('shopping_list.txt'),
            content_type='application/txt'
        )
        response['Content-Disposition'] = (
            'attachment; filename=shopping_list.txt'
        )
        response['Content-Type'] = 'application/txt'
        return response


class UsersViewSet(UserViewSet):
    """ViewSet for Users"""

    pagination_class = CustomPagination

    @action(detail=True, permission_classes=(IsAuthenticated,))
    def follow(self, request, pk):
        user = request.user
        author = get_object_or_404(User, id=pk)
        following = Follow.objects.create(user=user, author=author)
        serializer = FollowSerializer(following, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @follow.mapping.delete
    def delete_following(self, request, pk):
        follow = Follow.objects.filter(author__id=pk)
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
        queryset = User.objects.filter(following__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
