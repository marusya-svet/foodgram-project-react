from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """User model"""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'login',
        'password',
        'first_name',
        'last_name',
    ]
    email = models.EmailField(
        'email',
        max_length=254,
        unique=True
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'

    def __str__(self):
        return self.first_name


class Follow(models.Model):
    """Follow model"""

    user = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE
    )

    class Meta:
        models.constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='user_following_author'
            )
        ]
