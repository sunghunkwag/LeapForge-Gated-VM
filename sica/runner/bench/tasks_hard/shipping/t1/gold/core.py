from table import FLAT, PER_KG, FREE_OVER

def cost(weight_kg, subtotal):
    if subtotal >= FREE_OVER:
        return 0.0
    return round(FLAT + weight_kg * PER_KG, 2)
