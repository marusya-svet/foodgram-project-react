# Generated by Django 3.2 on 2023-12-19 12:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0004_alter_recipe_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredient',
            name='name',
            field=models.CharField(max_length=150, verbose_name='Ингредиент'),
        ),
    ]