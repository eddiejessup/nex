from string import ascii_letters, ascii_lowercase, ascii_uppercase, digits
from common import ascii_characters
from typer import (CatCode, WeirdChar, MathClass, GlyphCode, MathCode,
                   not_a_delimiter_code, ignored_delimiter_code)


class NotInScopeError(Exception):
    pass


def get_initial_char_cats():
    char_to_cat = {c: CatCode.other for c in ascii_characters}
    char_to_cat.update({let: CatCode.letter for let in ascii_letters})

    char_to_cat['\\'] = CatCode.escape
    char_to_cat[' '] = CatCode.space
    char_to_cat['%'] = CatCode.comment
    char_to_cat[WeirdChar.null.value] = CatCode.ignored
    # NON-STANDARD
    char_to_cat[WeirdChar.line_feed.value] = CatCode.end_of_line
    char_to_cat[WeirdChar.carriage_return.value] = CatCode.end_of_line
    char_to_cat[WeirdChar.delete.value] = CatCode.invalid
    return char_to_cat


def get_initial_char_math_codes():
    char_to_math_code = {}
    for i, c in enumerate(ascii_characters):
        if c in ascii_letters:
            family = 1
        else:
            family = 0
        if c in (ascii_letters + digits):
            math_class = MathClass.variable_family
        else:
            math_class = MathClass.ordinary
        glyph_code = GlyphCode(family=family, position=i)
        char_to_math_code[i] = MathCode(math_class, glyph_code)
        # TODO: handle special active_math_code value,
        # page 155 of The TeXbook.
    return char_to_math_code


def get_initial_case_codes():
    lower_case_code, upper_case_code = [
        {c: chr(0) for c in ascii_characters}
        for _ in range(2)
    ]
    for lower, upper in zip(ascii_lowercase, ascii_uppercase):
        lower_case_code[lower] = lower
        upper_case_code[upper] = upper
        lower_case_code[upper] = lower
        upper_case_code[lower] = upper
    return lower_case_code, upper_case_code


def get_initial_space_factor_codes():
    space_factor_code = {c: (999 if c in ascii_uppercase else 1000)
                         for c in ascii_characters}
    return space_factor_code


def get_initial_delimiter_codes():
    delimiter_code = {c: not_a_delimiter_code for c in ascii_characters}
    delimiter_code['.'] = ignored_delimiter_code
    return delimiter_code


class Scope(object):

    def __init__(self,
                 char_to_cat,
                 char_to_math_code,
                 lower_case_code, upper_case_code,
                 space_factor_code,
                 delimiter_code,
                 ):
        self.char_to_cat = char_to_cat
        self.char_to_math_code = char_to_math_code
        self.lower_case_code, self.upper_case_code = (lower_case_code,
                                                      upper_case_code)
        self.space_factor_code = space_factor_code
        self.delimiter_code = delimiter_code

        self.code_type_to_char_map = {
            'cat': self.char_to_cat,
            'math': self.char_to_math_code,
            'upper_case': self.upper_case_code,
            'lower_case': self.lower_case_code,
            'space_factor': self.space_factor_code,
            'delimiter': self.delimiter_code,
        }

    def set_code(self, code_type, char, code):
        char_map = self.code_type_to_char_map[code_type]
        char_map[char] = code

    def set_cat_code(self, char, cat):
        self.set_code('cat', char, cat)

    def set_math_code(self, char, code):
        self.set_code('math', char, code)

    def set_upper_case_code(self, char, up_char):
        self.set_code('upper_case', char, up_char)

    def set_lower_case_code(self, char, low_char):
        self.set_code('lower_case', char, low_char)

    def set_space_factor_code(self, char, code):
        self.set_code('space_factor', char, code)

    def set_delimiter_code(self, char, code):
        self.set_code('delimiter', char, code)

    def get_code(self, code_type, char):
        char_map = self.code_type_to_char_map[code_type]
        return char_map[char]

    def get_cat_code(self, char):
        return self.get_code('cat', char)

    def get_math_code(self, char):
        return self.get_code('math', char)

    def get_upper_case_code(self, char):
        return self.get_code('upper_case', char)

    def get_lower_case_code(self, char):
        return self.get_code('lower_case', char)

    def get_space_factor_code(self, char):
        return self.get_code('space_factor', char)

    def get_delimiter_code(self, char):
        return self.get_code('delimiter', char)


class GlobalSettings(object):

    pass


class GlobalState(object):

    def __init__(self):
        self.global_settings = GlobalSettings()
        self.scopes = []
        global_scope = self.get_global_scope()
        self.push_scope(global_scope)

    def get_global_scope(self):
        char_to_cat = get_initial_char_cats()
        char_to_math_code = get_initial_char_math_codes()
        lower_case_code, upper_case_code = get_initial_case_codes()
        space_factor_code = get_initial_space_factor_codes()
        delimiter_code = get_initial_delimiter_codes()
        global_scope = Scope(char_to_cat,
                             char_to_math_code,
                             lower_case_code, upper_case_code,
                             space_factor_code,
                             delimiter_code)
        return global_scope

    def get_local_scope(self):
        char_to_cat = {}
        char_to_math_code = {}
        lower_case_code, upper_case_code = {}, {}
        space_factor_code = {}
        delimiter_code = {}
        local_scope = Scope(char_to_cat,
                            char_to_math_code,
                            lower_case_code, upper_case_code,
                            space_factor_code,
                            delimiter_code)
        return local_scope

    def push_scope(self, scope):
        self.scopes.append(scope)

    def push_new_scope(self):
        scope = self.get_local_scope()
        self.scopes.append(scope)

    def pop_scope(self):
        self.scopes.pop()

    @property
    def scope(self):
        return self.scopes[-1]

    def set_cat_code(self, *args, **kwargs):
        self.scope.set_cat_code(*args, **kwargs)

    def set_math_code(self, *args, **kwargs):
        self.scope.set_math_code(*args, **kwargs)

    def set_upper_case_code(self, *args, **kwargs):
        self.scope.set_upper_case_code(*args, **kwargs)

    def set_lower_case_code(self, *args, **kwargs):
        self.scope.set_lower_case_code(*args, **kwargs)

    def set_space_factor_code(self, *args, **kwargs):
        self.scope.set_space_factor_code(*args, **kwargs)

    def set_delimiter_code(self, *args, **kwargs):
        self.scope.set_delimiter_code(*args, **kwargs)

    def try_scope_until_success(self, func_name, *args, **kwargs):
        for scope in reversed(self.scopes):
            f = getattr(scope, func_name)
            try:
                v = f(*args, **kwargs)
            except (NotInScopeError, KeyError):
                pass
            else:
                return v
        import pdb; pdb.set_trace()

    def get_cat_code(self, *args, **kwargs):
        return self.try_scope_until_success('get_cat_code', *args, **kwargs)

    def get_math_code(self, *args, **kwargs):
        return self.try_scope_until_success('get_math_code', *args, **kwargs)

    def get_lower_case_code(self, *args, **kwargs):
        return self.try_scope_until_success('get_lower_case_code', *args, **kwargs)

    def get_upper_case_code(self, *args, **kwargs):
        return self.try_scope_until_success('get_upper_case_code', *args, **kwargs)

    def get_space_factor_code(self, *args, **kwargs):
        return self.try_scope_until_success('get_space_factor_code', *args, **kwargs)

    def get_delimiter_code(self, *args, **kwargs):
        return self.try_scope_until_success('get_delimiter_code', *args, **kwargs)
