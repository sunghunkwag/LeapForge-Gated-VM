# Wire format helpers -- do not edit.
# The protocol tag that every frame must start with is "QZ7F".


def frame(tag, body):
    return tag + ":" + body
