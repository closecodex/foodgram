import csv
import os

from api.models import Ingredient
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

DATA_ROOT = os.path.join(settings.BASE_DIR, 'data')


class Command(BaseCommand):
    """Для загрузки ингредиентов"""

    def add_arguments(self, parser):
        parser.add_argument('filename', default='ingredients.csv', nargs='?',
                            type=str)

    def handle(self, *args, **options):
        file_path = os.path.join(DATA_ROOT, options['filename'])

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = csv.reader(f)
                for row in data:
                    name, measurement_unit = row
                    Ingredient.objects.get_or_create(
                        name=name,
                        measurement_unit=measurement_unit
                    )
            self.stdout.write(self.style.SUCCESS('Ингредиенты добавлены'))

        except FileNotFoundError:
            raise CommandError(
                f'File "{file_path}" does not exist.'
                'Please add it to the /data/ directory'
            )
