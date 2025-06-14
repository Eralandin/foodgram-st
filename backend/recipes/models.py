from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
# Create your models here.

User = get_user_model()


class Ingridient(models.Model):
    name = models.CharField(max_length=128, verbose_name='Название')
    measurement_unit = models.CharField(max_length=64,
                                        verbose_name='Единица измерения')

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиент'


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes')
    name = models.CharField(max_length=256, verbose_name='Название')
    test = models.TextField(verbose_name='Описание')
    image = models.ImageField(verbose_name='Картинка',
                              upload_to='recipes/', null=True, blank=True)
    cooking_time = models.IntegerField(validators=[MinValueValidator(1)],
                                       verbose_name='Время готовки')
    ingridients = models.ManyToManyField(Ingridient,
                                         through='UsedIngridients',
                                         verbose_name='Список ингредиентов')

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class UsedIngridients(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingridient = models.ForeignKey(Ingridient, on_delete=models.CASCADE)
    amount = models.IntegerField(validators=[MinValueValidator(1)],
                                 verbose_name='Используемое количество')
