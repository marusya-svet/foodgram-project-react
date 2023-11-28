from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

User = get_user_model()


class Ingredient(models.Model):
    """Ingredient model"""

    name = models.CharField('Ингредиеннт', max_length=150)
    measure_unit = models.CharField('Единица измерения', max_length=150)

    class Meta:
        verbose_name = 'Ингредиент'
        ordering = ['name']

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Tag model"""

    name = models.CharField('Название', unique=True, max_length=200)
    color_hex = models.CharField('HEX-код цвета', unique=True, max_length=7)
    slug = models.SlugField('Уникальный слаг', unique=True, max_length=200)

    class Meta:
        verbose_name = 'Тег'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Recipe model"""

    name = models.CharField('Название рецепта', max_length=200)
    description = models.TextField('Опиисание')
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    image = models.ImageField(
        'Фотография блюда',
        upload_to='recipes/',
        blank=True
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Тэги'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name='recipes',
        verbose_name='Ингредиенты',
        through='IngredientInRecipe'
    )
    cooking_time = models.PositiveIntegerField(
        'Время приготовления',
        validators=[MinValueValidator(1, message='min time is 1!'),]
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    """Ingredient in recipe model"""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_in_recipe',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.PositiveIntegerField(
        'Количество ингредиента',
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'

    def __str__(self):
        return self.ingredient.name


class Favorite(models.Model):
    """Model for adding recipe to favorites"""

    recipe = models.ForeignKey(
        Recipe,
        related_name='favorites',
        verbose_name='Избранный рецепт',
        on_delete=models.CASCADE
    )

    user = models.ForeignKey(
        User,
        related_name='favorites',
        verbose_name='Пользователь',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Избраннный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        models.constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='user_favorite_recipe'
            )
        ]

    def __str__(self):
        return f'{self.user} favorite {self.recipe}'


class ShoppingList(models.Model):
    """Model for recipes in shopping list"""

    recipe = models.ForeignKey(
        Recipe,
        related_name='shopping_recipe',
        verbose_name='Рецепт в листе покупок',
        on_delete=models.CASCADE
    )

    user = models.ForeignKey(
        User,
        related_name='shopping_recipe',
        verbose_name='Пользователь',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Рецепт в листе покупок'
        verbose_name_plural = 'Рецепты в листе покупок'
        models.constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='user_shopping_recipe'
            )
        ]

    def __str__(self):
        return f"{self.recipe} is in {self.user}'s shopping list"
