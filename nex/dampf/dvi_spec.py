from enum import Enum
import os.path

from .utils import get_bytes_needed


class EncodedValue:

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def nr_bytes(self):
        return len(self.encode())

    def __repr__(self):
        return '{}(name={}, value={})'.format(self.__class__.__name__,
                                              self.name, self.value)


class EncodedInteger(EncodedValue):

    def __init__(self, length, signed=False, allow_unsigned_4_byte=False,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not isinstance(self.value, int):
            raise TypeError('Trying to encode non-integer as integer')
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
    def name(self):
        return self.op_code.name

    @property
    def encoded_op_code(self):
        return EncodedOperation(self.op_code)

    @property
    def op_and_args(self):
        return [self.encoded_op_code] + self.arguments

    def encode(self):
        return b''.join(b.encode() for b in self.op_and_args)

    def __repr__(self):
        return '{}(name={}, arguments={})'.format(self.__class__.__name__,
                                                  self.name,
                                                  self.arguments)


def _encode_integer_to_bytes(length, value, signed=False,
                             allow_unsigned_4_byte=False):
    if not allow_unsigned_4_byte and length == 4:
        signed = True
    # 'DVI files use big endian format for multiple byte integer
    # parameters.'
    return value.to_bytes(length=length, signed=signed, byteorder='big')


class OpCode(Enum):

    # 0 to 127: set that character number.
    set_char_0 = 0
    set_char_1 = 1
    set_char_2 = 2
    set_char_3 = 3
    set_char_4 = 4
    set_char_5 = 5
    set_char_6 = 6
    set_char_7 = 7
    set_char_8 = 8
    set_char_9 = 9
    set_char_10 = 10
    set_char_11 = 11
    set_char_12 = 12
    set_char_13 = 13
    set_char_14 = 14
    set_char_15 = 15
    set_char_16 = 16
    set_char_17 = 17
    set_char_18 = 18
    set_char_19 = 19
    set_char_20 = 20
    set_char_21 = 21
    set_char_22 = 22
    set_char_23 = 23
    set_char_24 = 24
    set_char_25 = 25
    set_char_26 = 26
    set_char_27 = 27
    set_char_28 = 28
    set_char_29 = 29
    set_char_30 = 30
    set_char_31 = 31
    set_char_32 = 32
    set_char_33 = 33
    set_char_34 = 34
    set_char_35 = 35
    set_char_36 = 36
    set_char_37 = 37
    set_char_38 = 38
    set_char_39 = 39
    set_char_40 = 40
    set_char_41 = 41
    set_char_42 = 42
    set_char_43 = 43
    set_char_44 = 44
    set_char_45 = 45
    set_char_46 = 46
    set_char_47 = 47
    set_char_48 = 48
    set_char_49 = 49
    set_char_50 = 50
    set_char_51 = 51
    set_char_52 = 52
    set_char_53 = 53
    set_char_54 = 54
    set_char_55 = 55
    set_char_56 = 56
    set_char_57 = 57
    set_char_58 = 58
    set_char_59 = 59
    set_char_60 = 60
    set_char_61 = 61
    set_char_62 = 62
    set_char_63 = 63
    set_char_64 = 64
    set_char_65 = 65
    set_char_66 = 66
    set_char_67 = 67
    set_char_68 = 68
    set_char_69 = 69
    set_char_70 = 70
    set_char_71 = 71
    set_char_72 = 72
    set_char_73 = 73
    set_char_74 = 74
    set_char_75 = 75
    set_char_76 = 76
    set_char_77 = 77
    set_char_78 = 78
    set_char_79 = 79
    set_char_80 = 80
    set_char_81 = 81
    set_char_82 = 82
    set_char_83 = 83
    set_char_84 = 84
    set_char_85 = 85
    set_char_86 = 86
    set_char_87 = 87
    set_char_88 = 88
    set_char_89 = 89
    set_char_90 = 90
    set_char_91 = 91
    set_char_92 = 92
    set_char_93 = 93
    set_char_94 = 94
    set_char_95 = 95
    set_char_96 = 96
    set_char_97 = 97
    set_char_98 = 98
    set_char_99 = 99
    set_char_100 = 100
    set_char_101 = 101
    set_char_102 = 102
    set_char_103 = 103
    set_char_104 = 104
    set_char_105 = 105
    set_char_106 = 106
    set_char_107 = 107
    set_char_108 = 108
    set_char_109 = 109
    set_char_110 = 110
    set_char_111 = 111
    set_char_112 = 112
    set_char_113 = 113
    set_char_114 = 114
    set_char_115 = 115
    set_char_116 = 116
    set_char_117 = 117
    set_char_118 = 118
    set_char_119 = 119
    set_char_120 = 120
    set_char_121 = 121
    set_char_122 = 122
    set_char_123 = 123
    set_char_124 = 124
    set_char_125 = 125
    set_char_126 = 126
    set_char_127 = 127

    set_1_byte_char = 128
    set_2_byte_char = 129
    set_3_byte_char = 130
    set_4_byte_char = 131

    set_rule = 132

    put_1_byte_char = 133
    put_2_byte_char = 134
    put_3_byte_char = 135
    put_4_byte_char = 136

    put_rule = 137

    no_op = 138

    begin_page = 139
    end_page = 140

    push = 141
    pop = 142

    right_1_byte = 143
    right_2_byte = 144
    right_3_byte = 145
    right_4_byte = 146

    right_w = 147
    set_1_byte_w_then_right_w = 148
    set_2_byte_w_then_right_w = 149
    set_3_byte_w_then_right_w = 150
    set_4_byte_w_then_right_w = 151

    right_x = 152
    set_1_byte_x_then_right_x = 153
    set_2_byte_x_then_right_x = 154
    set_3_byte_x_then_right_x = 155
    set_4_byte_x_then_right_x = 156

    down_1_byte = 157
    down_2_byte = 158
    down_3_byte = 159
    down_4_byte = 160

    down_y = 161
    set_1_byte_y_then_down_y = 162
    set_2_byte_y_then_down_y = 163
    set_3_byte_y_then_down_y = 164
    set_4_byte_y_then_down_y = 165

    down_z = 166
    set_1_byte_z_then_down_z = 167
    set_2_byte_z_then_down_z = 168
    set_3_byte_z_then_down_z = 169
    set_4_byte_z_then_down_z = 170

    # 171 to 234: Select font number.
    select_font_nr_0 = 171
    select_font_nr_1 = 172
    select_font_nr_2 = 173
    select_font_nr_3 = 174
    select_font_nr_4 = 175
    select_font_nr_5 = 176
    select_font_nr_6 = 177
    select_font_nr_7 = 178
    select_font_nr_8 = 179
    select_font_nr_9 = 180
    select_font_nr_10 = 181
    select_font_nr_11 = 182
    select_font_nr_12 = 183
    select_font_nr_13 = 184
    select_font_nr_14 = 185
    select_font_nr_15 = 186
    select_font_nr_16 = 187
    select_font_nr_17 = 188
    select_font_nr_18 = 189
    select_font_nr_19 = 190
    select_font_nr_20 = 191
    select_font_nr_21 = 192
    select_font_nr_22 = 193
    select_font_nr_23 = 194
    select_font_nr_24 = 195
    select_font_nr_25 = 196
    select_font_nr_26 = 197
    select_font_nr_27 = 198
    select_font_nr_28 = 199
    select_font_nr_29 = 200
    select_font_nr_30 = 201
    select_font_nr_31 = 202
    select_font_nr_32 = 203
    select_font_nr_33 = 204
    select_font_nr_34 = 205
    select_font_nr_35 = 206
    select_font_nr_36 = 207
    select_font_nr_37 = 208
    select_font_nr_38 = 209
    select_font_nr_39 = 210
    select_font_nr_40 = 211
    select_font_nr_41 = 212
    select_font_nr_42 = 213
    select_font_nr_43 = 214
    select_font_nr_44 = 215
    select_font_nr_45 = 216
    select_font_nr_46 = 217
    select_font_nr_47 = 218
    select_font_nr_48 = 219
    select_font_nr_49 = 220
    select_font_nr_50 = 221
    select_font_nr_51 = 222
    select_font_nr_52 = 223
    select_font_nr_53 = 224
    select_font_nr_54 = 225
    select_font_nr_55 = 226
    select_font_nr_56 = 227
    select_font_nr_57 = 228
    select_font_nr_58 = 229
    select_font_nr_59 = 230
    select_font_nr_60 = 231
    select_font_nr_61 = 232
    select_font_nr_62 = 233
    select_font_nr_63 = 234

    select_1_byte_font_nr = 235
    select_2_byte_font_nr = 236
    select_3_byte_font_nr = 237
    select_4_byte_font_nr = 238

    do_1_byte_special = 239
    do_2_byte_special = 240
    do_3_byte_special = 241
    do_4_byte_special = 242

    define_1_byte_font_nr = 243
    define_2_byte_font_nr = 244
    define_3_byte_font_nr = 245
    define_4_byte_font_nr = 246

    preamble = 247
    postamble = 248
    post_postamble = 249


no_arg_char_op_codes = [OpCode[f'set_char_{i}']
                        for i in range(128)]
no_arg_select_font_nr_op_codes = [OpCode[f'select_font_nr_{i}']
                                  for i in range(63)]


def get_simple_instruction_func(op_code, *string_getters):
    def get_instruction(*values):
        if len(values) != len(string_getters):
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

get_put_rule_instruction = get_simple_instruction_func(OpCode.put_rule, g(4, name='height'), g(4, name='width'))
get_set_rule_instruction = get_simple_instruction_func(OpCode.set_rule, g(4, name='height'), g(4, name='width'))

# Characters.

get_put_1_byte_char_instruction = get_simple_instruction_func(OpCode.put_1_byte_char, g(1, name='char'))
get_put_2_byte_char_instruction = get_simple_instruction_func(OpCode.put_2_byte_char, g(2, name='char'))
get_put_3_byte_char_instruction = get_simple_instruction_func(OpCode.put_3_byte_char, g(3, name='char'))
get_put_4_byte_char_instruction = get_simple_instruction_func(OpCode.put_4_byte_char, g(4, name='char'))

get_set_1_byte_char_instruction = get_simple_instruction_func(OpCode.set_1_byte_char, g(1, name='char'))
get_set_2_byte_char_instruction = get_simple_instruction_func(OpCode.set_2_byte_char, g(2, name='char'))
get_set_3_byte_char_instruction = get_simple_instruction_func(OpCode.set_3_byte_char, g(3, name='char'))
get_set_4_byte_char_instruction = get_simple_instruction_func(OpCode.set_4_byte_char, g(4, name='char'))

# Movers.

get_right_w_instruction = get_simple_instruction_func(OpCode.right_w)
get_right_x_instruction = get_simple_instruction_func(OpCode.right_x)
get_down_y_instruction = get_simple_instruction_func(OpCode.down_y)
get_down_z_instruction = get_simple_instruction_func(OpCode.down_z)

get_right_1_byte_instruction = get_simple_instruction_func(OpCode.right_1_byte, g(1, True, name='distance'))
get_right_2_byte_instruction = get_simple_instruction_func(OpCode.right_2_byte, g(2, True, name='distance'))
get_right_3_byte_instruction = get_simple_instruction_func(OpCode.right_3_byte, g(3, True, name='distance'))
get_right_4_byte_instruction = get_simple_instruction_func(OpCode.right_4_byte, g(4, True, name='distance'))

get_set_1_byte_w_then_right_w_instruction = get_simple_instruction_func(OpCode.set_1_byte_w_then_right_w, g(1, True, name='distance'))
get_set_2_byte_w_then_right_w_instruction = get_simple_instruction_func(OpCode.set_2_byte_w_then_right_w, g(2, True, name='distance'))
get_set_3_byte_w_then_right_w_instruction = get_simple_instruction_func(OpCode.set_3_byte_w_then_right_w, g(3, True, name='distance'))
get_set_4_byte_w_then_right_w_instruction = get_simple_instruction_func(OpCode.set_4_byte_w_then_right_w, g(4, True, name='distance'))

get_set_1_byte_x_then_right_x_instruction = get_simple_instruction_func(OpCode.set_1_byte_x_then_right_x, g(1, True, name='distance'))
get_set_2_byte_x_then_right_x_instruction = get_simple_instruction_func(OpCode.set_2_byte_x_then_right_x, g(2, True, name='distance'))
get_set_3_byte_x_then_right_x_instruction = get_simple_instruction_func(OpCode.set_3_byte_x_then_right_x, g(3, True, name='distance'))
get_set_4_byte_x_then_right_x_instruction = get_simple_instruction_func(OpCode.set_4_byte_x_then_right_x, g(4, True, name='distance'))

get_down_1_byte_instruction = get_simple_instruction_func(OpCode.down_1_byte, g(1, True, name='distance'))
get_down_2_byte_instruction = get_simple_instruction_func(OpCode.down_2_byte, g(2, True, name='distance'))
get_down_3_byte_instruction = get_simple_instruction_func(OpCode.down_3_byte, g(3, True, name='distance'))
get_down_4_byte_instruction = get_simple_instruction_func(OpCode.down_4_byte, g(4, True, name='distance'))

get_set_1_byte_y_then_down_y_instruction = get_simple_instruction_func(OpCode.set_1_byte_y_then_down_y, g(1, True, name='distance'))
get_set_2_byte_y_then_down_y_instruction = get_simple_instruction_func(OpCode.set_2_byte_y_then_down_y, g(2, True, name='distance'))
get_set_3_byte_y_then_down_y_instruction = get_simple_instruction_func(OpCode.set_3_byte_y_then_down_y, g(3, True, name='distance'))
get_set_4_byte_y_then_down_y_instruction = get_simple_instruction_func(OpCode.set_4_byte_y_then_down_y, g(4, True, name='distance'))

get_set_1_byte_z_then_down_z_instruction = get_simple_instruction_func(OpCode.set_1_byte_z_then_down_z, g(1, True, name='distance'))
get_set_2_byte_z_then_down_z_instruction = get_simple_instruction_func(OpCode.set_2_byte_z_then_down_z, g(2, True, name='distance'))
get_set_3_byte_z_then_down_z_instruction = get_simple_instruction_func(OpCode.set_3_byte_z_then_down_z, g(3, True, name='distance'))
get_set_4_byte_z_then_down_z_instruction = get_simple_instruction_func(OpCode.set_4_byte_z_then_down_z, g(4, True, name='distance'))

# Font selection.

get_select_1_byte_font_nr_instruction = get_simple_instruction_func(OpCode.select_1_byte_font_nr, g(1, name='font_number'))
get_select_2_byte_font_nr_instruction = get_simple_instruction_func(OpCode.select_2_byte_font_nr, g(2, name='font_number'))
get_select_3_byte_font_nr_instruction = get_simple_instruction_func(OpCode.select_3_byte_font_nr, g(3, name='font_number'))
get_select_4_byte_font_nr_instruction = get_simple_instruction_func(OpCode.select_4_byte_font_nr, g(4, name='font_number'))

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
    op_code = OpCode(char)
    if op_code not in no_arg_char_op_codes:
        raise ValueError(f'Character {char} cannot be set with a small '
                         f'instruction')
    return EncodedInstruction(op_code)


def get_small_select_font_nr_instruction(font_nr):
    op_code_nr = font_nr + OpCode.select_font_nr_0.value
    op_code = OpCode(op_code_nr)
    if op_code not in no_arg_select_font_nr_op_codes:
        raise ValueError(f'Cannot select font number {font_nr}')
    return EncodedInstruction(op_code)


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
