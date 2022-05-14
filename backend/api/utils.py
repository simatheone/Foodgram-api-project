from recipes.models import RecipeIngredientAmount


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
    Function returns a list with ingredients.
    Some ingredients could be repeated.
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
