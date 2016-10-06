from enum import Enum
import os.path

from .utils import get_bytes_needed


class EncodedValue(object):

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def nr_bytes(self):
        return len(self.encode())


class EncodedInteger(EncodedValue):

    def __init__(self, length, signed=False, allow_unsigned_4_byte=False,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.length = length
        self.signed = signed
        self.allow_unsigned_4_byte = allow_unsigned_4_byte

    def encode(self):
        return _encode_integer_to_bytes(self.length, self.value, self.signed,
                                        self.allow_unsigned_4_byte)

    @property
    def value_as_int(self):
        return int.from_bytes(self.value, byteorder='big')

    def __repr__(self):
        return '{}(name={}, value={}, length={})'.format(self.__class__.__name__,
                                                         self.name, self.value,
                                                         self.length)


class EncodedOperation(EncodedValue):

    def __init__(self, op_code):
        self.op_code = op_code

    @property
    def name(self):
        return self.op_code.name

    @property
    def value(self):
        return self.op_code.value

    def encode(self):
        return _encode_integer_to_bytes(length=1, value=self.value,
                                        signed=False)

    def __repr__(self):
        return '{}(name={})'.format(self.__class__.__name__, self.name)


class EncodedString(EncodedValue):

    def encode(self):
        return self.value.encode(encoding='ascii')

    def __repr__(self):
        return '{}(name={}, value={}, length={})'.format(self.__class__.__name__,
                                                         self.name, self.value,
                                                         len(self.value))


class EncodedInstruction(EncodedValue):

    def __init__(self, op_code, *arguments):
        self.op_code = op_code
        self.arguments = list(arguments)

    @property
    def encoded_op_code(self):
        return EncodedOperation(self.op_code)

    @property
    def op_and_args(self):
        return [self.encoded_op_code] + self.arguments

    def encode(self):
        return b''.join(b.encode() for b in self.op_and_args)


def _encode_integer_to_bytes(length, value, signed=False,
                             allow_unsigned_4_byte=False):
    if not allow_unsigned_4_byte and length == 4:
        signed = True
    try:
        # 'DVI files use big endian format for multiple byte integer
        # parameters.'
        return value.to_bytes(length=length, signed=signed, byteorder='big')
    except:
        import pdb; pdb.set_trace()


op_codes = {
    # 0 to 127: set that character number.

    'set_1_byte_char': 128,
    'set_2_byte_char': 129,
    'set_3_byte_char': 130,
    'set_4_byte_char': 131,

    'set_rule': 132,

    'put_1_byte_char': 133,
    'put_2_byte_char': 134,
    'put_3_byte_char': 135,
    'put_4_byte_char': 136,

    'put_rule': 137,

    'no_op': 138,

    'begin_page': 139,
    'end_page': 140,

    'push': 141,
    'pop': 142,

    'right_1_byte': 143,
    'right_2_byte': 144,
    'right_3_byte': 145,
    'right_4_byte': 146,

    'right_w': 147,
    'set_1_byte_w_then_right_w': 148,
    'set_2_byte_w_then_right_w': 149,
    'set_3_byte_w_then_right_w': 150,
    'set_4_byte_w_then_right_w': 151,

    'right_x': 152,
    'set_1_byte_x_then_right_x': 153,
    'set_2_byte_x_then_right_x': 154,
    'set_3_byte_x_then_right_x': 155,
    'set_4_byte_x_then_right_x': 156,

    'down_1_byte': 157,
    'down_2_byte': 158,
    'down_3_byte': 159,
    'down_4_byte': 160,

    'down_y': 161,
    'set_1_byte_y_then_down_y': 162,
    'set_2_byte_y_then_down_y': 163,
    'set_3_byte_y_then_down_y': 164,
    'set_4_byte_y_then_down_y': 165,

    'down_z': 166,
    'set_1_byte_z_then_down_z': 167,
    'set_2_byte_z_then_down_z': 168,
    'set_3_byte_z_then_down_z': 169,
    'set_4_byte_z_then_down_z': 170,

    # 171 to 234: Select font number.

    'select_1_byte_font_nr': 235,
    'select_2_byte_font_nr': 236,
    'select_3_byte_font_nr': 237,
    'select_4_byte_font_nr': 238,

    'do_1_byte_special': 239,
    'do_2_byte_special': 240,
    'do_3_byte_special': 241,
    'do_4_byte_special': 242,

    'define_1_byte_font_nr': 243,
    'define_2_byte_font_nr': 244,
    'define_3_byte_font_nr': 245,
    'define_4_byte_font_nr': 246,

    'preamble': 247,
    'postamble': 248,
    'post_postamble': 249,
}
no_arg_char_op_codes = list(range(128))
op_codes.update({'set_char_{}'.format(i): i
                 for i in no_arg_char_op_codes})
no_arg_select_font_nr_op_codes = list(range(171, 235))
op_codes.update({'select_font_nr_{}'.format(i): i
                 for i in no_arg_select_font_nr_op_codes})
OpCode = Enum('OpCode', op_codes)


def get_simple_instruction_func(op_code, *string_getters):
    def get_instruction(*values):
        if not len(values) == len(string_getters):
            raise ValueError
        encodeds = []
        for string_getter, value in zip(string_getters, values):
            encodeds.append(string_getter(value))
        return EncodedInstruction(op_code, *encodeds)
    return get_instruction


def g(length, signed=False, name=''):
    return lambda v: EncodedInteger(length=length, signed=signed, value=v,
                                    name=name)


def get_define_font_nr_instruction_func(op_code, font_nr_length_bytes):
    def get_define_font_nr_instruction(font_nr, check_sum,
                                       scale_factor, design_size,
                                       font_path):
        font_nr_encoded = EncodedInteger(length=font_nr_length_bytes,
                                         value=font_nr,
                                         name='font_nr')
        check_sum_encoded = EncodedInteger(length=4, value=check_sum,
                                           name='check_sum',
                                           allow_unsigned_4_byte=True)
        scale_factor_encoded = EncodedInteger(length=4, value=scale_factor,
                                              name='scale_factor')
        design_size_encoded = EncodedInteger(length=4, value=design_size,
                                             name='design_size')

        dir_path, file_name = os.path.split(font_path)

        dir_path_length_encoded = EncodedInteger(1, value=len(dir_path),
                                                 name='dir_path_length')
        file_name_length_encoded = EncodedInteger(1, value=len(file_name),
                                                  name='file_name_length')

        font_path_encoded = EncodedString(value=font_path, name='font_path')

        return EncodedInstruction(op_code, font_nr_encoded, check_sum_encoded,
                                  scale_factor_encoded, design_size_encoded,
                                  dir_path_length_encoded,
                                  file_name_length_encoded, font_path_encoded)
    return get_define_font_nr_instruction


def get_do_special_instruction_func(op_code, command_length_bytes):
    def get_do_special_instruction(command):
        command_length_encoded = EncodedInteger(length=command_length_bytes,
                                                value=len(command))
        command_encoded = EncodedString(value=command, name='special_command')
        return EncodedInstruction(op_code,
                                  command_length_encoded, command_encoded)
    return get_do_special_instruction

# Rules.

get_put_rule_instruction = get_simple_instruction_func(OpCode.put_rule, g(4), g(4))
get_set_rule_instruction = get_simple_instruction_func(OpCode.set_rule, g(4), g(4))

# Characters.

get_put_1_byte_char_instruction = get_simple_instruction_func(OpCode.put_1_byte_char, g(1))
get_put_2_byte_char_instruction = get_simple_instruction_func(OpCode.put_2_byte_char, g(2))
get_put_3_byte_char_instruction = get_simple_instruction_func(OpCode.put_3_byte_char, g(3))
get_put_4_byte_char_instruction = get_simple_instruction_func(OpCode.put_4_byte_char, g(4))

get_set_1_byte_char_instruction = get_simple_instruction_func(OpCode.set_1_byte_char, g(1))
get_set_2_byte_char_instruction = get_simple_instruction_func(OpCode.set_2_byte_char, g(2))
get_set_3_byte_char_instruction = get_simple_instruction_func(OpCode.set_3_byte_char, g(3))
get_set_4_byte_char_instruction = get_simple_instruction_func(OpCode.set_4_byte_char, g(4))

# Movers.

get_right_w_instruction = get_simple_instruction_func(OpCode.right_w)
get_right_x_instruction = get_simple_instruction_func(OpCode.right_x)
get_down_y_instruction = get_simple_instruction_func(OpCode.down_y)
get_down_z_instruction = get_simple_instruction_func(OpCode.down_z)

get_right_1_byte_instruction = get_simple_instruction_func(OpCode.right_1_byte, g(1, True))
get_right_2_byte_instruction = get_simple_instruction_func(OpCode.right_2_byte, g(2, True))
get_right_3_byte_instruction = get_simple_instruction_func(OpCode.right_3_byte, g(3, True))
get_right_4_byte_instruction = get_simple_instruction_func(OpCode.right_4_byte, g(4, True))

get_set_1_byte_w_then_right_w_instruction = get_simple_instruction_func(OpCode.set_1_byte_w_then_right_w, g(1, True))
get_set_2_byte_w_then_right_w_instruction = get_simple_instruction_func(OpCode.set_2_byte_w_then_right_w, g(2, True))
get_set_3_byte_w_then_right_w_instruction = get_simple_instruction_func(OpCode.set_3_byte_w_then_right_w, g(3, True))
get_set_4_byte_w_then_right_w_instruction = get_simple_instruction_func(OpCode.set_4_byte_w_then_right_w, g(4, True))

get_set_1_byte_x_then_right_x_instruction = get_simple_instruction_func(OpCode.set_1_byte_x_then_right_x, g(1, True))
get_set_2_byte_x_then_right_x_instruction = get_simple_instruction_func(OpCode.set_2_byte_x_then_right_x, g(2, True))
get_set_3_byte_x_then_right_x_instruction = get_simple_instruction_func(OpCode.set_3_byte_x_then_right_x, g(3, True))
get_set_4_byte_x_then_right_x_instruction = get_simple_instruction_func(OpCode.set_4_byte_x_then_right_x, g(4, True))

get_down_1_byte_instruction = get_simple_instruction_func(OpCode.down_1_byte, g(1, True))
get_down_2_byte_instruction = get_simple_instruction_func(OpCode.down_2_byte, g(2, True))
get_down_3_byte_instruction = get_simple_instruction_func(OpCode.down_3_byte, g(3, True))
get_down_4_byte_instruction = get_simple_instruction_func(OpCode.down_4_byte, g(4, True))

get_set_1_byte_y_then_down_y_instruction = get_simple_instruction_func(OpCode.set_1_byte_y_then_down_y, g(1, True))
get_set_2_byte_y_then_down_y_instruction = get_simple_instruction_func(OpCode.set_2_byte_y_then_down_y, g(2, True))
get_set_3_byte_y_then_down_y_instruction = get_simple_instruction_func(OpCode.set_3_byte_y_then_down_y, g(3, True))
get_set_4_byte_y_then_down_y_instruction = get_simple_instruction_func(OpCode.set_4_byte_y_then_down_y, g(4, True))

get_set_1_byte_z_then_down_z_instruction = get_simple_instruction_func(OpCode.set_1_byte_z_then_down_z, g(1, True))
get_set_2_byte_z_then_down_z_instruction = get_simple_instruction_func(OpCode.set_2_byte_z_then_down_z, g(2, True))
get_set_3_byte_z_then_down_z_instruction = get_simple_instruction_func(OpCode.set_3_byte_z_then_down_z, g(3, True))
get_set_4_byte_z_then_down_z_instruction = get_simple_instruction_func(OpCode.set_4_byte_z_then_down_z, g(4, True))

# Font selection.

get_select_1_byte_font_nr_instruction = get_simple_instruction_func(OpCode.select_1_byte_font_nr, g(1))
get_select_2_byte_font_nr_instruction = get_simple_instruction_func(OpCode.select_2_byte_font_nr, g(2))
get_select_3_byte_font_nr_instruction = get_simple_instruction_func(OpCode.select_3_byte_font_nr, g(3))
get_select_4_byte_font_nr_instruction = get_simple_instruction_func(OpCode.select_4_byte_font_nr, g(4))

# Special.

get_do_1_byte_special_instruction = get_do_special_instruction_func(OpCode.do_1_byte_special, 1)
get_do_2_byte_special_instruction = get_do_special_instruction_func(OpCode.do_2_byte_special, 2)
get_do_3_byte_special_instruction = get_do_special_instruction_func(OpCode.do_3_byte_special, 3)
get_do_4_byte_special_instruction = get_do_special_instruction_func(OpCode.do_4_byte_special, 4)

# Font definition.

get_define_1_byte_font_nr_instruction = get_define_font_nr_instruction_func(OpCode.define_1_byte_font_nr, 1)
get_define_2_byte_font_nr_instruction = get_define_font_nr_instruction_func(OpCode.define_2_byte_font_nr, 2)
get_define_3_byte_font_nr_instruction = get_define_font_nr_instruction_func(OpCode.define_3_byte_font_nr, 3)
get_define_4_byte_font_nr_instruction = get_define_font_nr_instruction_func(OpCode.define_4_byte_font_nr, 4)

# Page start and end.
begin_page_parameters = ([g(4, name='c_{}'.format(i)) for i in range(10)] +
                         [g(4, name='previous_begin_page_pointer')])
get_begin_page_instruction = get_simple_instruction_func(OpCode.begin_page,
                                                         *begin_page_parameters)
get_end_page_instruction = get_simple_instruction_func(OpCode.end_page)


# Miscellaneous

get_push_instruction = get_simple_instruction_func(OpCode.push)
get_pop_instruction = get_simple_instruction_func(OpCode.pop)
get_no_op_instruction = get_simple_instruction_func(OpCode.no_op)


# Explicit op-codes for setting characters and selecting fonts.

def get_small_set_char_instruction_func(char):
    if char not in no_arg_char_op_codes:
        raise ValueError
    op_code_nr = char
    return EncodedInstruction(OpCode(op_code_nr))


def get_small_select_font_nr_instruction(font_nr):
    if font_nr not in no_arg_select_font_nr_op_codes:
        raise ValueError
    op_code_nr = font_nr + no_arg_select_font_nr_op_codes[0]
    return EncodedInstruction(OpCode(op_code_nr))


postamble_parameters = [
    g(4, name='final_begin_page_pointer'),  # Pointer to final Opcode.begin_page.
    # Re-iteration of numbers in preamble.
    g(4, name='numerator'),  # Numerator.
    g(4, name='denominator'),  # Denominator.
    g(4, name='mag'),  # Magnification.
    # These are in the same units as other dimensions in the file.
    g(4, name='max_page_height_plus_depth'),  # Height-plus-depth of the tallest page.
    g(4, name='max_page_width'),  # Width of the widest page.
    g(2, name='max_stack_depth'),  # Maximum stack depth needed (biggest (pushes - pops)).
    g(2, name='nr_pages'),  # Total number of pages (number of OpCode.begin_page's).
]
get_postamble_instruction = get_simple_instruction_func(OpCode.postamble,
                                                        *postamble_parameters)


def get_preamble_instruction(dvi_format, numerator, denominator, magnification,
                             comment):
    dvi_format_encoded = EncodedInteger(length=1, value=dvi_format,
                                        name='dvi_format')
    # Define a fraction by which all dimensions should be multiplied to get
    # lengths in units of 10^(-7) meters.
    numerator_encoded = EncodedInteger(length=4, value=numerator,
                                       name='numerator')
    denominator_encoded = EncodedInteger(length=4, value=denominator,
                                         name='denominator')

    # 1000 times the magnification (\mag in TeX).
    magnification_encoded = EncodedInteger(length=4, value=magnification,
                                           name='mag')

    comment_length_encoded = EncodedInteger(length=1, value=len(comment),
                                            name='comment_len')
    comment_encoded = EncodedString(value=comment, name='comment')

    encodeds = EncodedInstruction(OpCode.preamble,
                                  dvi_format_encoded, numerator_encoded,
                                  denominator_encoded, magnification_encoded,
                                  comment_length_encoded, comment_encoded)
    return encodeds


signature_integer = 223


def get_post_postamble_instruction(postamble_pointer, dvi_format):
    # Pointer to OpCode.postamble.
    postamble_pointer_encoded = EncodedInteger(length=4,
                                               value=postamble_pointer,
                                               name='postamble_pointer')
    # DVI format, as in preamble.
    dvi_format_encoded = EncodedInteger(length=1, value=dvi_format,
                                        name='dvi_format')
    # We can finish with four or more '223's, but any will do.
    signature_encodeds = [EncodedInteger(length=1, value=signature_integer,
                                         name='signature')
                          for _ in range(4)]

    encodeds = EncodedInstruction(OpCode.post_postamble,
                                  postamble_pointer_encoded,
                                  dvi_format_encoded, *signature_encodeds)
    return encodeds


# Abstractions to avoid worrying about numbers of bytes.

get_do_special_instruction_funcs = [
    get_do_1_byte_special_instruction,
    get_do_2_byte_special_instruction,
    get_do_3_byte_special_instruction,
    get_do_4_byte_special_instruction,
]

get_put_char_instruction_funcs = [
    get_put_1_byte_char_instruction,
    get_put_2_byte_char_instruction,
    get_put_3_byte_char_instruction,
    get_put_4_byte_char_instruction,
]

get_big_set_char_instruction_funcs = [
    get_set_1_byte_char_instruction,
    get_set_2_byte_char_instruction,
    get_set_3_byte_char_instruction,
    get_set_4_byte_char_instruction,
]

get_right_instruction_funcs = [
    get_right_1_byte_instruction,
    get_right_2_byte_instruction,
    get_right_3_byte_instruction,
    get_right_4_byte_instruction,
]

get_set_w_then_right_w_instruction_funcs = [
    get_set_1_byte_w_then_right_w_instruction,
    get_set_2_byte_w_then_right_w_instruction,
    get_set_3_byte_w_then_right_w_instruction,
    get_set_4_byte_w_then_right_w_instruction,
]

get_set_x_then_right_x_instruction_funcs = [
    get_set_1_byte_x_then_right_x_instruction,
    get_set_2_byte_x_then_right_x_instruction,
    get_set_3_byte_x_then_right_x_instruction,
    get_set_4_byte_x_then_right_x_instruction,
]

get_down_instruction_funcs = [
    get_down_1_byte_instruction,
    get_down_2_byte_instruction,
    get_down_3_byte_instruction,
    get_down_4_byte_instruction,
]

get_set_y_then_down_y_instruction_funcs = [
    get_set_1_byte_y_then_down_y_instruction,
    get_set_2_byte_y_then_down_y_instruction,
    get_set_3_byte_y_then_down_y_instruction,
    get_set_4_byte_y_then_down_y_instruction,
]

get_set_z_then_down_z_instruction_funcs = [
    get_set_1_byte_z_then_down_z_instruction,
    get_set_2_byte_z_then_down_z_instruction,
    get_set_3_byte_z_then_down_z_instruction,
    get_set_4_byte_z_then_down_z_instruction,
]

get_big_select_font_nr_instruction_funcs = [
    get_select_1_byte_font_nr_instruction,
    get_select_2_byte_font_nr_instruction,
    get_select_3_byte_font_nr_instruction,
    get_select_4_byte_font_nr_instruction,
]

get_define_font_nr_instruction_funcs = [
    get_define_1_byte_font_nr_instruction,
    get_define_2_byte_font_nr_instruction,
    get_define_3_byte_font_nr_instruction,
    get_define_4_byte_font_nr_instruction,
]


def _get_func_on_bytes(n, funcs, signed):
    nr_bytes_needed = get_bytes_needed(n, signed=signed)
    return funcs[nr_bytes_needed - 1]


def _scatter_instruction(signed, get_instruction_funcs):
    def get_instruction_func(main_val, *args, **kwargs):
        base_get_instruction_func = _get_func_on_bytes(main_val,
                                                       get_instruction_funcs,
                                                       signed=signed)
        return base_get_instruction_func(main_val, *args, **kwargs)
    return get_instruction_func


def get_set_char_instruction(char):
    if char in no_arg_char_op_codes:
        return get_small_set_char_instruction_func(char)
    else:
        base_get_instruction_func = _get_func_on_bytes(char,
                                                       get_big_set_char_instruction_funcs,
                                                       signed=False)
        return base_get_instruction_func(char)


def get_select_font_nr_instruction(font_nr):
    if font_nr in no_arg_select_font_nr_op_codes:
        return get_small_select_font_nr_instruction(font_nr)
    else:
        base_get_instruction_func = _get_func_on_bytes(font_nr,
                                                       get_big_select_font_nr_instruction_funcs,
                                                       signed=False)
        return base_get_instruction_func(font_nr)


def get_do_special_instruction(command):
    base_get_instruction_func = _get_func_on_bytes(len(command),
                                                   get_do_special_instruction_funcs,
                                                   signed=False)
    return base_get_instruction_func(command)


get_put_char_instruction = _scatter_instruction(False, get_put_char_instruction_funcs)
get_right_instruction = _scatter_instruction(True, get_right_instruction_funcs)
get_set_w_then_right_w_instruction = _scatter_instruction(True, get_set_w_then_right_w_instruction_funcs)
get_set_x_then_right_x_instruction = _scatter_instruction(True, get_set_x_then_right_x_instruction_funcs)
get_down_instruction = _scatter_instruction(True, get_down_instruction_funcs)
get_set_y_then_down_y_instruction = _scatter_instruction(True, get_set_y_then_down_y_instruction_funcs)
get_set_z_then_down_z_instruction = _scatter_instruction(True, get_set_z_then_down_z_instruction_funcs)
get_define_font_nr_instruction = _scatter_instruction(True, get_define_font_nr_instruction_funcs)
