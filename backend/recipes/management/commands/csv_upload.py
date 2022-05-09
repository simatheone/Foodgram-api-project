import csv
from pathlib import Path

from django.core.management.base import BaseCommand
from recipes.models import Ingredient
from foodgram.settings import BASE_DIR

def ingredient_create(row):
    Ingredient.objects.get_or_create(
        name=row[0],
        measurement_unit=row[1]
    )

action = {
    'ingredients.csv': ingredient_create
}

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        path = str(BASE_DIR.parent.joinpath('data').resolve()) + '/'
        for key in action:
            with open(path + key, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)
                for row in reader:
                    action[key](row)