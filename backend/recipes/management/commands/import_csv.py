import csv

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


def import_ingredient():
    """Function for importing ingredient models"""

    if Ingredient.objects.exists():
        print('Данные для этой модели уже выгружены')
    else:
        with open(
            f'{settings.BASE_DIR}/static/data/ingredients.csv',
            'r', encoding='utf-8'
        ) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                Ingredient.objects.create(
                    name=row['name'],
                    measure_unit=row['measure_unit'],
                )


class Command(BaseCommand):
    """Вызов функции"""

    def handle(self, *args, **options):
        import_ingredient()
        self.stdout.write(self.style.SUCCESS('Data imported successfully'))
