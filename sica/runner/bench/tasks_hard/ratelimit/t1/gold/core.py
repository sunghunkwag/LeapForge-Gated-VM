from limits import LIMIT

def allowed(plan, used):
    return used < LIMIT[plan]
