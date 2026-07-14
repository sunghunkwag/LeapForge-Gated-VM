def cost(weight_kg, subtotal):
    if subtotal >= 50.0:
        return 0.0
    return 5.0 + weight_kg * 2.0
