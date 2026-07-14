"""csvlite: a tiny CSV record parser (quotes and escaped commas), pure string ops."""


def parse_line(line):
    """Parse a single CSV record into a list of string fields.

    Rules:
      * Fields are separated by commas.
      * A field may be wrapped in double quotes; a comma inside a quoted field
        is a literal character, not a separator.
      * Inside a quoted field, a doubled quote ("") is an escape that denotes a
        single literal double-quote character.
    """
    fields = []
    buf = []
    i = 0
    n = len(line)
    in_quotes = False
    while i < n:
        c = line[i]
        if in_quotes:
            if c == '"':
                if i + 1 < n and line[i + 1] == '"':
                    buf.append('"')
                    i += 2
                    continue
                in_quotes = False
                i += 1
            else:
                buf.append(c)
                i += 1
        else:
            if c == '"':
                in_quotes = True
                i += 1
            elif c == ',':
                fields.append("".join(buf))
                buf = []
                i += 1
            else:
                buf.append(c)
                i += 1
    fields.append("".join(buf))
    return fields
