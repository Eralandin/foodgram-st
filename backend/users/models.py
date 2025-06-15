from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError


class User(AbstractUser):
    email = models.EmailField(unique=True, max_length=254,
                              verbose_name='Адрес эл. почты')
    username = models.CharField(max_length=150, unique=True,
                                verbose_name='Имя пользователя',
                                validators=[RegexValidator(
                                    regex=r"^[\w.@+-]+\Z"
                                )])
    first_name = models.CharField(max_length=150,
                                  verbose_name='Имя')
    last_name = models.CharField(max_length=150,
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


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="following",
        verbose_name="Пользователь"
    )
    follower = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="follower",
        verbose_name="Подписчик"
    )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def clean(self):
        if self.user == self.follower:
            raise ValidationError(
                "Подписка на себя недопустима."
            )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        ordering = ['user__username',]
        unique_together = (
            'user',
            'follower',
        )
