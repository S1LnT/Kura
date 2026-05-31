def do():
    return "$"

def to_int(value):
    try:
        return int(value)
    except ValueError:
        return 0  # Or handle the error as needed
