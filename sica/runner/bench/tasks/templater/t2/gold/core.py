def render(tmpl, values):
    SENT_L, SENT_R = '\x00L', '\x00R'
    out = tmpl.replace('{{', SENT_L).replace('}}', SENT_R)
    for k, v in values.items():
        out = out.replace('{' + k + '}', str(v))
    return out.replace(SENT_L, '{').replace(SENT_R, '}')
