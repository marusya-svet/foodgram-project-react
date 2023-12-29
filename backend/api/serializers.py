import base64

from django.core.files.base import ContentFile
from django.db.models import F
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
                  'last_name', 'is_subscribed', 'password']

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

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measure_unit = serializers.ReadOnlyField(source='ingredient.measure_unit')
    amount = serializers.IntegerField(
        min_value=MIN_INGREDIENT_AMOUNT,
        max_value=MAX_INGREDIENT_AMOUNT,
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

    author = UserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all())
    ingredients = IngredientInRecipeSerializer(many=True)
    image = Base64ImageField(required=False, allow_null=True)
    is_in_favorites = serializers.SerializerMethodField()
    is_in_shopping_list = serializers.SerializerMethodField()
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME,
        max_value=MAX_COOKING_TIME,
    )

    class Meta:
        model = Recipe
        fields = ['id', 'author', 'name',
                  'description', 'image',
                  'cooking_time', 'tags',
                  'ingredients', 'is_in_favorites',
                  'is_in_shopping_list']

    def get_ingredients(self, recipe):
        ingredients = recipe.ingredients.values(
            'id', 'name', 'measure_unit', amount=F('recipe__amount')
        )
        return ingredients

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

    @staticmethod
    def create_ingredients_amount(recipe, ingredients):
        obj = []
        for ingredient in ingredients:
            obj.append(
                IngredientInRecipe(
                    ingredient=ingredient.pop('id'),
                    amount=ingredient.pop('amount'),
                    recipe=recipe,
                )
            )
        IngredientInRecipe.objects.bulk_create(obj)

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

    @atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients_amount(recipe, ingredients)
        return recipe

    @atomic
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
