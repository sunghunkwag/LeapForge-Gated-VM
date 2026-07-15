def allowed(plan, used):
    caps = {'free': 20, 'pro': 200, 'enterprise': 2000}
    return used < caps[plan]
