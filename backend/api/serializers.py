import base64
from django.core.files.base import ContentFile
from rest_framework import serializers
from djoser.serializers import UserSerializer

from recipes.models import (
    Recipe,
    IngredientInRecipe,
    Ingredient,
    Tag)
from users.models import User, Follow

MIN_INGREDIENT_AMOUNT = 1
MAX_INGREDIENT_AMOUNT = 32000
MIN_COOKING_TIME = 1
MAX_COOKING_TIME = 3200


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

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed']

    def get_is_subscribed(self, obj):
        user = self.context.get('user')
        if user.is_anonymous:
            return False
        return user.following.exists()


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredient model"""

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measure_unit']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model"""

    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'slug']


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Serializer for IngredientInRecipe model"""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measure_unit = serializers.ReadOnlyField(source='ingredient.measure_unit')
    amount = serializers.IntegerField(
        min_length=MIN_INGREDIENT_AMOUNT,
        max_length=MAX_INGREDIENT_AMOUNT,
    )

    class Meta:
        model = IngredientInRecipe
        fields = ['id', 'name', 'measure_unit', 'amount']


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for Recipe model"""

    author = UsersSerializer(read_only=True)
    tags = TagSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer()
    image = Base64ImageField()
    is_in_favorites = serializers.SerializerMethodField()
    is_in_shopping_list = serializers.SerializerMethodField()
    cooking_time = serializers.IntegerField(
        min_length=MIN_COOKING_TIME,
        max_length=MAX_COOKING_TIME,
    )

    class Meta:
        model = Recipe
        fields = ['id', 'author', 'name',
                  'description', 'image',
                  'cooking_time', 'tags',
                  'ingredients', 'is_in_favorites',
                  'is_in_shopping_list']

    def get_is_in_favorites(self, obj):
        user = self.context.get('user')
        if user.is_anonymous:
            return False
        return Recipe.objects.filter(favorites__user=user, id=obj.id)

    def get_is_in_shopping_list(self, obj):
        user = self.context.get('user')
        if user.is_anonymous:
            return False
        return Recipe.objects.filter(list__user=user, id=obj.id)

    def create_ingredients_amount(self, ingredients, recipe):
        IngredientInRecipe.objects.bulk_create(
            [IngredientInRecipe(
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                recipe=recipe,
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )

    def validate(self, data):
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError({'tags': 'Need to choose tag'})
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError()
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Need to choose ingredient'}
            )
        if len(ingredients) != len(set(ingredients)):
            raise serializers.ValidationError('ingredients must be unique')
        return data

    def create(self, validated_data):
        recipe = Recipe.objects.create(**validated_data)
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get(
            'description', instance.description
        )
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.tags.clear()
        tags_new = self.initial_data.get('tags')
        instance.tags.set(tags_new)
        instance.ingredients.clear()
        self.create_ingredients_amount(
            validated_data.get('ingredients'),
            instance)
        instance.save()
        return instance


class AddIngredientSerializer(serializers.ModelSerializer):
    """Serializer for adding ingredient in recipe"""

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ['id', 'amount']


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
        return obj.following.exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        queryset = obj.recipes.all()
        if limit:
            queryset = queryset[:int(limit)]
        return ShortRecipeSerializer(queryset, many=True).data
