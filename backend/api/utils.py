from recipes.models import RecipeIngredientAmount


def shopping_cart_dict(recipes_list):

    ingredient_list = []
    for values in recipes_list:
        recipe = values.recipe
        ingredient_obj = RecipeIngredientAmount.objects.filter(recipe=recipe)
        ingredient_list.append(ingredient_obj)

    list_of_ingredients = []
    for value in ingredient_list:
        for ingredient in value:
            values = (
                ingredient.ingredient.name,
                ingredient.amount,
                ingredient.ingredient.measurement_unit
            )
            list_of_ingredients.append(values)
    
    ingredients_for_repr = {}
    for value in list_of_ingredients:
        if value[0] in ingredients_for_repr and (
           ingredients_for_repr[value[0]]['measurement_unit'] == value[2]
        ):
           ingredients_for_repr[value[0]]['amount'] += value[1]
        else:
            ingredients_for_repr[value[0]] = {
                'amount': value[1],
                'measurement_unit': value[2] 
            }
    return ingredients_for_repr
