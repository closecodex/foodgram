from django.contrib.auth.models import AbstractUser
from django.db import models

from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Модель пользователя."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    validator_username = UnicodeUsernameValidator()

    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        unique=True,
        blank=False,
        null=False,
        error_messages={
            'unique': 'Этот адрес уже используется',
        },
    )
    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=150,
        validators=[validator_username],
        unique=True,
        blank=False,
        null=False,
        error_messages={
            'unique': 'Пользователь с этим именем уже существует',
        },
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=150,
        blank=False,
        null=False,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=150,
        blank=False,
        null=False,
    )
    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='avatars/',
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username