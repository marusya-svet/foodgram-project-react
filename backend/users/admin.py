from django.contrib import admin

from .models import User, Subscribe


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'password'
    )
    list_filter = (
        'email',
        'username',
    )
    list_editable = ('password',)
    search_fields = ('username', 'email')


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'author'
    )
