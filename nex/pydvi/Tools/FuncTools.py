__all__ = ['repeat_call']


def repeat_call(func, count):
    """ Call the function *func* *count* times and return the output as a list. """

    return [func() for i in range(count)]
