def render(tmpl, values):
    out = tmpl
    for k, v in values.items():
        out = out.replace('{' + k + '}', str(v), 1)
    return out
