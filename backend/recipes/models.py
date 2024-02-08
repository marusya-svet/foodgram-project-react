from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

User = get_user_model()

MIN_COOKING_TIME = 1
MAX_COOKING_TIME = 3200
MIN_INGREDIENT_AMOUNT = 1
MAX_INGREDIENT_AMOUNT = 32000


class Ingredient(models.Model):
    """Ingredient model"""

    name = models.CharField('Ингредиент', max_length=150)
    measure_unit = models.CharField('Единица измерения', max_length=150)

    class Meta:
        verbose_name = 'Ингредиент'
        ordering = ['id']

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Tag model"""

    name = models.CharField('Название',
                            unique=True,
                            max_length=200,)
    color_hex = models.CharField('HEX-код цвета',
                                 unique=True,
                                 max_length=7,
                                 db_index=False)
    slug = models.SlugField('Уникальный слаг',
                            unique=True,
                            max_length=200,
                            db_index=False)

    class Meta:
        verbose_name = 'Тег'
        ordering = ['id']

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Recipe model"""

    name = models.CharField('Название рецепта', max_length=200)
    text = models.TextField('Опиисание')
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.SET_NULL,
        verbose_name='Автор',
        null=True
    )
    image = models.ImageField(
        'Фотография блюда',
        upload_to='recipes/',
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
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=(
            MinValueValidator(
                MIN_COOKING_TIME, message='min time is 1!'
            ),
            MaxValueValidator(
                MAX_COOKING_TIME, message='max time is 3200'
            )
        )
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        editable=False,
        default=timezone.now,
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class IngredientInRecipe(models.Model):
    """Ingredient in recipe model"""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredienttorecipe',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество ингредиента',
        default=0,
        validators=(
            MinValueValidator(
                MIN_INGREDIENT_AMOUNT, message='min amount is 1!'
            ),
            MaxValueValidator(
                MAX_INGREDIENT_AMOUNT, message='max amount is 32000'
            )
        )
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        ordering = ['id']

    def __str__(self):
        return self.ingredient.name


class Favorite(models.Model):
    """Model for adding recipe to favorites"""

    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='favorites'
    )

    recipe = models.ForeignKey(
        Recipe,
        related_name='favorites',
        verbose_name='Избранный рецепт',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Избраннный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        ordering = ['id']
        models.constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='user_favorite_recipe'
            )
        ]

    def __str__(self):
        return f'{self.user} favorite {self.recipe}'


class ShoppingCart(models.Model):
    """Model for recipes in shopping list"""

    user = models.ForeignKey(
        User,
        related_name='shopping_cart',
        verbose_name='Пользователь',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='shopping_cart',
        verbose_name='Рецепт в листе покупок',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Рецепт в листе покупок'
        verbose_name_plural = 'Рецепты в листе покупок'
        ordering = ['id']
        models.constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='user_shopping_recipe'
            )
        ]

    def __str__(self):
        return f"{self.recipe} is in {self.user}s shopping cart"
