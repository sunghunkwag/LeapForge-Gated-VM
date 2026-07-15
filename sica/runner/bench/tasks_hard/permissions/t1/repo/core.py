def can(role, needed):
    levels = {'guest': 0, 'member': 1, 'editor': 2, 'admin': 3}
    return levels[role] >= needed
