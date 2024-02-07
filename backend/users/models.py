from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """User model"""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    email = models.EmailField(
        'email',
        max_length=254,
        unique=True
    )

    class Meta:
        verbose_name = 'Пользователь'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    """Follow model"""

    user = models.ForeignKey(
        to=User,
        related_name='subscriber',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        to=User,
        related_name='subscribing',
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
