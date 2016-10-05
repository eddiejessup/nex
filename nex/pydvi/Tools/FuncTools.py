__all__ = ['repeat_call', 'get_filename_extension']


def repeat_call(func, count):
    """ Call the function *func* *count* times and return the output as a list. """

    return [func() for i in range(count)]


def get_filename_extension(filename):
    """ Return the filename extension. """

    index = filename.rfind('.')
    if index >= 0:
        try:
            return filename[index+1:]
        except:
            return None
    else:
        return None


def sign_of(x):
    """ Return the sign of a number. """
    if x < 0:
        return -1
    else:
        return 1

# def sign(x):
#     return cmp(x, 0)


def middle(a, b):
    return .5 * (a + b)
