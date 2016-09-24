import base64
import uuid


def increasing_window(a):
    for i_max in range(len(a) + 1):
        yield a[:i_max]


def get_unique_id():
    raw = uuid.uuid4()
    compressed = base64.urlsafe_b64encode(raw.bytes).decode("utf-8")
    sanitised = compressed.rstrip('=\n').replace('/', '_')
    return sanitised


class NoSuchControlSequence(Exception):
    pass
