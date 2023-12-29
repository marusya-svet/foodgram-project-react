import base64

from django.core.files.base import ContentFile
from django.db.transaction import atomic
from django.contrib.auth import get_user_model
from rest_framework import serializers

from recipes.models import (
    Recipe,
    IngredientInRecipe,
    Ingredient,
    Tag)
from users.models import Follow

MIN_INGREDIENT_AMOUNT = 1
MAX_INGREDIENT_AMOUNT = 32000
MIN_COOKING_TIME = 1
MAX_COOKING_TIME = 3200

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Field for codding image to base64"""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed']

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous or (user == obj):
            return False
        return user.following.exists()

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredient model"""

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measure_unit']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model"""

    class Meta:
        model = Tag
        fields = ['id', 'name', 'color_hex', 'slug']


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Serializer for IngredientInRecipe model"""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measure_unit = serializers.ReadOnlyField(source='ingredient.measure_unit')

    class Meta:
        model = IngredientInRecipe
        fields = ['id', 'name', 'measure_unit', 'amount']


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        many=True,
        source='ingredienttorecipe')
    is_in_favorite = serializers.SerializerMethodField()
    is_in_shopping_list = serializers.SerializerMethodField()
    image = Base64ImageField(required=False)
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME,
        max_value=MAX_COOKING_TIME,
    )

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'tags', 'ingredients',
                  'is_in_favorite', 'is_in_shopping_list',
                  'name', 'text', 'image', 'cooking_time')

    def get_ingredients(self, obj):
        ingredients = IngredientInRecipe.objects.filter(recipe=obj)
        return IngredientInRecipeSerializer(ingredients, many=True).data

    def get_is_in_favorite(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Recipe.objects.filter(favorites__user=request.user, id=obj.id)

    def get_is_in_shopping_list(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Recipe.objects.filter(shopping_recipe__user=request.user, id=obj.id)


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Serializer for Recipe model"""

    author = UserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all())
    ingredients = IngredientInRecipeSerializer(many=True)
    image = Base64ImageField(required=False, allow_null=True)
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME,
        max_value=MAX_COOKING_TIME,
    )

    class Meta:
        model = Recipe
        fields = ['id', 'author', 'name', 'text',
                  'image', 'cooking_time', 'tags',
                  'ingredients']

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
        return data

    @staticmethod
    def create_ingredients(recipe, ingredients):
        ingredient_list = []
        for ingredient_data in ingredients:
            ingredient_list.append(
                IngredientInRecipe(
                    ingredient=ingredient_data.pop('id'),
                    amount=ingredient_data.pop('amount'),
                    recipe=recipe,
                )
            )
        IngredientInRecipe.objects.bulk_create(ingredient_list)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.tags.clear()
        IngredientInRecipe.objects.filter(recipe=instance).delete()
        instance.tags.set(validated_data.pop('tags'))
        ingredients = validated_data.pop('ingredients')
        self.create_ingredients(instance, ingredients)
        return super().update(instance, validated_data)


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
    recipes = ShortRecipeSerializer(many=True, read_only=True)
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
