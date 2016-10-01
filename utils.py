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


def sum_infinities(ds):
    order_sums = [0]
    for d in ds:
        if isinstance(d, int):
            order_sums[0] += d
        else:
            order = d.value['number_of_fils']
            # Extend order sum list with zeros to accommodate this infinity.
            new_length_needed = order + 1 - len(order_sums)
            order_sums.extend(0 for _ in range(new_length_needed))
            order_sums[order] += d.value['factor']
    return order_sums
