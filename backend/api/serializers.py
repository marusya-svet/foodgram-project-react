import base64
from django.core.files.base import ContentFile
from rest_framework import serializers
from djoser.serializers import UserSerializer

from recipes.models import (Recipe, IngredientInRecipe, Ingredient,
                            Tag, Favorite, ShoppingList)
from users.models import User, Follow


class Base64ImageField(serializers.ImageField):
    """Field for codding image to base64"""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class UsersSerializer(UserSerializer):
    """Serializer for User model"""

    id_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed']

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj.id).exists()


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredient model"""

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measure_unit']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model"""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Serializer for IngredientInRecipe model"""

    name = serializers.CharField(
        source='ingredient.name', read_only=True
    )
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient.id', read_only=True
    )
    measure_unit = serializers.CharField(
        source='ingredient.measure_unit', read_only=True
    )

    class Meta:
        model = IngredientInRecipe
        fields = ['id', 'name', 'measure_unit', 'amount']


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for Recipe model"""


class FollowSerializer(UserSerializer):
    """Serializer for adding or deleting subscription.
    And for showing the following list"""

    user = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    following = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field='username',
        read_only=False
    )
    recipes = RecipeSerializer(many=True, read_only=True)
    count_recipes = serializers.SerializerMethodField(read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = ['user', 'following', 'recipes',
                  'count_recipes', 'is_subscribed']
        validators = (
            serializers.UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('user', 'following')
            ),
        )

    def validate_following(self, value):
        if value == self.context['request'].user:
            raise serializers.ValidationError('так нельзя')
        return value

    def get_count_recipes(self, obj):
        return obj.recipes.count()

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(author=obj.author).exists()


