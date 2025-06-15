from django.db import models
from django.core.validators import MinValueValidator
from users.models import User


class Ingredient(models.Model):
    name = models.CharField(max_length=128, verbose_name='Название')
    measurement_unit = models.CharField(max_length=64,
                                        verbose_name='Единица измерения')

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиент'


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes',
        related_query_name='recipe')
    name = models.CharField(max_length=256, verbose_name='Название')
    text = models.TextField(verbose_name='Описание')
    image = models.ImageField(verbose_name='Картинка',
                              upload_to='recipes/')
    cooking_time = models.IntegerField(validators=[MinValueValidator(1)],
                                       verbose_name='Время готовки')
    ingredients = models.ManyToManyField(Ingredient,
                                         through='UsedIngredients',
                                         verbose_name='Список ингредиентов')

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class UsedIngredients(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='recipeName')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   related_name='ingredientsList')
    amount = models.PositiveIntegerField(validators=[MinValueValidator(1)],
                                         verbose_name=(
                                             ('Используемое количество')))

    class Meta:
        verbose_name = 'Ингредиент, используемый в рецепте'
        verbose_name_plural = 'Ингредиенты, используемые в рецепте'
        unique_together = ('recipe', 'ingredient')


class Favorite(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='favorite',
        verbose_name='Избранный рецепт'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='favorites',
        verbose_name='Пользователь'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class UserToRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        unique_together = ('user', 'recipe')


class ShoppingCart(UserToRecipe):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shoppingCart'
    )
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='shoppingcart')

    class Meta():
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
