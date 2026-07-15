import re
_RE = re.compile(r'^\d+\.\d+\.\d+$')

def is_valid(s):
    return bool(_RE.match(s))
