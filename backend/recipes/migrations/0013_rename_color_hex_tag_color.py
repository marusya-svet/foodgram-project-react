# Generated by Django 3.2 on 2024-02-09 11:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0012_rename_measure_unit_ingredient_measurement_unit'),
    ]

    operations = [
        migrations.RenameField(
            model_name='tag',
            old_name='color_hex',
            new_name='color',
        ),
    ]
