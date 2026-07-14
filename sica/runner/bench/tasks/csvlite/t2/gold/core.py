"""csvlite: a tiny CSV record parser (quotes and escaped commas), pure string ops."""


def parse_line(line):
    """Parse a single CSV record into a list of string fields.

    Rules:
      * Fields are separated by commas.
      * A double quote opens a quoted field ONLY when it is the first character
        of the field. Inside a quoted field a comma is literal and a doubled
        quote ("") decodes to one literal quote character.
      * A double quote that appears after other characters in a field is an
        ordinary literal character, not a quote delimiter.
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
            if c == '"' and not buf:
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
