import io
from pathlib import Path

from django.db.models import Sum
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from recipes.models import RecipeIngredientAmount

CART_TITLE = 'СПИСОК ПОКУПОК'
EMPTY_CART_TITLE = 'Список покупок пуст'
FONTS_DIR = Path('./static/fonts/DejaVuSerif.ttf').resolve()


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
    x_value, y_value = 20, 635

    # Get all ingredients with it's name, amount (unique), measurement_unit
    # Which are in request user's shopping cart
    ingredients_list = RecipeIngredientAmount.objects.filter(
        recipe__shopping_cart__user=user
    ).values('ingredient__name', 'ingredient__measurement_unit').annotate(
        total_amount=Sum('amount')
    )

    if ingredients_list:
        pdf_page.drawCentredString(315, 700, CART_TITLE)

        for value in ingredients_list:
            name = value['ingredient__name'].capitalize()
            amount = value['total_amount']
            measure = value['ingredient__measurement_unit']
            write_string = f'{name} - {amount} ({measure});'
            pdf_page.drawString(
                x_value, y_value, write_string
            )
            y_value -= 30
        pdf_page.save()
        buffer.seek(0)
        return buffer

    pdf_page.drawCentredString(315, 425, EMPTY_CART_TITLE)
    pdf_page.showPage()
    pdf_page.save()
    buffer.seek(0)
    return buffer
