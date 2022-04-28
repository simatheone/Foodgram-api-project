from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import CheckConstraint, F, UniqueConstraint, Q
from django.db.models.deletion import CASCADE


USER_ROLE_USER = 'user'
USER_ROLE_ADMIN = 'admin'

USER_ROLE_CHOICES = (
    (USER_ROLE_USER, 'Пользователь'),
    (USER_ROLE_ADMIN, 'Администратор')
)


class CustomUser(AbstractUser):
    """CustomUser model."""

    username = models.CharField(
        'username',
        max_length=150,
        unique=True
    )
    first_name = models.CharField(
        'Имя',
        max_length=150
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=150
    )
    email = models.EmailField(
        'Электронная почта',
        max_length=254,
        unique=True, 
    )
    role = models.CharField(
        'Роль',
        max_length=15,
        choices=USER_ROLE_CHOICES,
        default=USER_ROLE_USER
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'password']

    class Meta:
        db_table = 'custom_user'
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = [
            models.UniqueConstraint(
                fields=('username', 'email'), name='unique_username_email'
            )
        ]

    def __str__(self):
        return f'Пользователь {self.username}'


class Subscription(models.Model):
    """Subscription model."""

    user = models.ForeignKey(
        CustomUser,
        related_name='sub_user',
        on_delete=CASCADE
    )
    author = models.ForeignKey(
        CustomUser,
        related_name='sub_author',
        on_delete=CASCADE
    )

    class Meta:
        db_table='subscription'
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            UniqueConstraint(
                fields=['user', 'author'], name='unique_subscription'
            ),
            CheckConstraint(check=~Q(user=F('author')),
                            name='user_cant_follow_himself'),
        ]

    def __str__(self):
        return f'{self.user} подписался на {self.author}'
