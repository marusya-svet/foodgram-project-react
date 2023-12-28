from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """User model"""

    email = models.EmailField(
        'email',
        max_length=254,
        unique=True
    )
    username = models.CharField(
        verbose_name='unique username',
        max_length=150,
        unique=True,
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
        ordering = ('username',)

    def __str__(self):
        return self.username


class Follow(models.Model):
    """Follow model"""

    user = models.ForeignKey(
        to=User,
        related_name='follower',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        to=User,
        related_name='following',
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ('-id',)
        models.constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='user_following_author'
            )
        ]

    def __str__(self):
        return f'{self.user.username} follows {self.author.username}'
