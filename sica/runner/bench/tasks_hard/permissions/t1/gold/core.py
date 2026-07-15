from roles import ROLE_LEVEL

def can(role, needed):
    return ROLE_LEVEL[role] >= needed
