from bands import BANDS

def grade(score):
    for lo, letter in BANDS:
        if score >= lo:
            return letter
    return 'F'
