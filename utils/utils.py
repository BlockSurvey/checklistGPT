import json


def is_json(value):
    if isinstance(value, (str, bytes, bytearray)):
        try:
            json_object = json.loads(value)
            return True
        except ValueError as e:
            return False
    elif isinstance(value, dict):
        return True
    return False