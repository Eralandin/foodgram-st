from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


class User(AbstractUser):
    email = models.EmailField(unique=True, max_length=254,
                              verbose_name='Адрес эл. почты')
    username = models.CharField(max_length=150, unique=True,
                                verbose_name='Имя пользователя',
                                validators=[RegexValidator(
                                    regex="^[\w.@+-]+\Z"
                                )])
    first_name = models.CharField(max_length=150, blank=True,
                                  verbose_name='Имя')
    last_name = models.CharField(max_length=150, blank=True,
                                 verbose_name='Фамилия')
    avatar = models.ImageField(
        upload_to='users/', null=True, blank=True,
        verbose_name='Аватар пользователя'
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
