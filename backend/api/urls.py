from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (IngredientViewSet,
                       TagViewSet,
                       RecipeViewSet,
                       UsersViewSet)

app_name = 'api'

router = DefaultRouter()
router.register('users', UsersViewSet, 'users')
router.register('tags', TagViewSet, 'tags')
router.register('ingredients', IngredientViewSet, 'ingredients')
router.register('recipes', RecipeViewSet, 'recipes')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
