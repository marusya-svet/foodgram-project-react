from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """User model"""

    username = models.CharField(
        'username',
        max_length=150,
        unique=True
    )
    email = models.EmailField(
        'email',
        max_length=254,
        unique=True
    )
    first_name = models.CharField(
        'first_name',
        max_length=150,
    )
    last_name = models.CharField(
        'last_name',
        max_length=150
    )
    password = models.CharField(
        'password',
        max_length=150
    )

    class Meta:
        verbose_name = 'Пользователь'

    def __str__(self):
        return self.username


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
