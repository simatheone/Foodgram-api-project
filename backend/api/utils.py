import io

from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from foodgram.settings import BASE_DIR
from recipes.models import RecipeIngredientAmount

CART_TITLE = 'СПИСОК ПОКУПОК'
EMPTY_CART_TITLE = 'Список покупок пуст'
FONTS_DIR = BASE_DIR.joinpath('static/fonts/DejaVuSerif.ttf')


def get_shopping_cart_for_writing(recipes_list):
    """
    Function returns dictionary with prepared ingredients.
    All ingredients are unique.
    Dictionary schema: {
        'ingredient_name': {
            'amount': int amount,
            'measurement_unit': str unit
        }
    }
    """
    ingredient_list = get_ingredients(recipes_list)
    ingredients_for_repr = {}
    for ingr in ingredient_list:
        if ingr[0] in ingredients_for_repr and (
           ingredients_for_repr[ingr[0]]['measurement_unit'] == ingr[2]
           ):
            ingredients_for_repr[ingr[0]]['amount'] += ingr[1]
        else:
            ingredients_for_repr[ingr[0]] = {
                'amount': ingr[1],
                'measurement_unit': ingr[2]
            }
    return ingredients_for_repr


def get_ingredients(recipes_list):
    """
    Function returns a list with lists of ingredients.
    Some ingredients could be repeated.
    List schema example:
        [
            [str: potato, int: 2, str: kg.],
            [str: lemon, int: 2, str: pieces],
            ...
            ...
        ]
    """
    ingredient_list = []
    for values in recipes_list:
        recipe_obj = values.recipe
        ingredient_obj = RecipeIngredientAmount.objects.filter(
            recipe=recipe_obj).order_by()
        for ingredient in ingredient_obj:
            ingredient_list.append(
                [
                    ingredient.ingredient.name,
                    ingredient.amount,
                    ingredient.ingredient.measurement_unit
                ]
            )
    return ingredient_list


def create_pdf_shopping_cart(user):
    """
    Function returns FileResponse (PDF File for downloading).
    If recipe/recipes have been added to shopping cart
    PDF would be filled with unique ingredients with its
    amounts and mesurement units.
    Otherwise it will be written 'Shopping cart is empty'.
    """
    buffer = io.BytesIO()
    pdf_page = canvas.Canvas(buffer, pagesize=letter)

    # Set fonts for pdf file
    pdfmetrics.registerFont(TTFont('DejaVuSerif', FONTS_DIR))
    pdf_page.setFont('DejaVuSerif', 14)

    # Set x and y positions for the text on the page
    x_value, y_value = 20, 600

    recipes_list = user.shopping_cart.all()
    # Calling a function from utils
    ingredients_list = get_shopping_cart_for_writing(recipes_list)

    if recipes_list:
        pdf_page.drawCentredString(315, 700, CART_TITLE)

        for value in ingredients_list:
            name = value.capitalize()
            amount = ingredients_list[value]['amount']
            measure = ingredients_list[value]['measurement_unit']
            write_string = f'{name} - {amount} ({measure});'
            pdf_page.drawString(
                x_value, y_value, write_string
            )
            y_value -= 30
        pdf_page.save()
        buffer.seek(0)
        return buffer
    else:
        pdf_page.drawCentredString(315, 425, EMPTY_CART_TITLE)
        pdf_page.showPage()
        pdf_page.save()
        buffer.seek(0)
        return buffer
