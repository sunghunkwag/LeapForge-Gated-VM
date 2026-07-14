import re
_RE = re.compile(r'^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$')

def is_valid(s):
    return bool(_RE.match(s))
