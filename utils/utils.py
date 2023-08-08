import json
import validators
from flask import g


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


def get_user_id():
    userId = ""
    if g.get('jwt_session', {}).get('sub', None) is None:
        return
    else:
        userId = g.jwt_session.get('sub')

    return userId


def is_valid_url(url: str):
    if not validators.url(url):
        return False

    return True
