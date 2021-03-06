from ..pydvi.Font.TfmParser import TfmParser
from ..pydvi.TeXUnit import pt2sp

from .dvi_spec import (get_set_char_instruction,
                       get_set_rule_instruction,
                       get_put_char_instruction,
                       get_put_rule_instruction,

                       get_no_op_instruction,

                       get_begin_page_instruction,
                       get_end_page_instruction,

                       get_push_instruction,
                       get_pop_instruction,

                       get_right_instruction,
                       get_right_w_instruction,
                       get_set_w_then_right_w_instruction,
                       get_right_x_instruction,
                       get_set_x_then_right_x_instruction,

                       get_down_instruction,
                       get_down_y_instruction,
                       get_set_y_then_down_y_instruction,
                       get_down_z_instruction,
                       get_set_z_then_down_z_instruction,

                       get_define_font_nr_instruction,
                       get_select_font_nr_instruction,

                       get_do_special_instruction,

                       get_preamble_instruction,
                       get_postamble_instruction,
                       get_post_postamble_instruction,
                       )
from .dvi_spec import EncodedOperation, EncodedInteger, EncodedString, OpCode

numerator = int(254e5)
denominator = int(7227 * 2 ** 16)
dvi_format = 2


class DVIDocument:

    def __init__(self, magnification):
        self.magnification = magnification

        self.preamble = get_preamble_instruction(dvi_format=dvi_format,
                                                 numerator=numerator,
                                                 denominator=denominator,
                                                 magnification=self.magnification,
                                                 comment='')
        self.mundane_instructions = []
        self.defined_fonts_info = {}
        self.stack_depth = 0
        self.max_stack_depth = self.stack_depth
        self.current_font_nr = None

    @property
    def instructions(self):
        return [self.preamble] + self.mundane_instructions

    @property
    def flat_instruction_parts(self):
        return [p for inst in self.instructions for p in inst.op_and_args]

    def op_code_pointers(self, op_code):
        byte_pointer = 0
        op_code_pointers = []
        for part in self.flat_instruction_parts:
            byte_pointer += part.nr_bytes()
            if (isinstance(part, EncodedOperation)
                    and part.op_code == op_code):
                op_code_pointers.append(byte_pointer - 1)
        return op_code_pointers

    @property
    def _begin_page_pointers(self):
        return self.op_code_pointers(OpCode.begin_page)

    @property
    def last_begin_page_pointer(self):
        pointers = self._begin_page_pointers
        return pointers[-1] if pointers else -1

    @property
    def nr_begin_page_pointers(self):
        return len(self._begin_page_pointers)

    def begin_new_page(self):
        # If we have any previous pages, need to end the last one.
        if self._begin_page_pointers:
            self._end_page()
        bop_args = list(range(10)) + [self.last_begin_page_pointer]
        bop = get_begin_page_instruction(*bop_args)
        self.mundane_instructions.append(bop)
        if self.current_font_nr is not None:
            self.select_font(self.current_font_nr)

    def _end_page(self):
        eop = get_end_page_instruction()
        self.mundane_instructions.append(eop)

    def define_font(self, font_nr, font_name, font_path,
                    scale_factor_ratio=1.0):
        font_info = TfmParser.parse(font_name, font_path)
        design_size = int(pt2sp(font_info.design_font_size))
        scale_factor = int(design_size * scale_factor_ratio)
        font_path = font_info.font_name
        define_font_nr_instr = get_define_font_nr_instruction(font_nr,
                                                              font_info.checksum,
                                                              scale_factor,
                                                              design_size,
                                                              font_path)
        self._define_font(define_font_nr_instr)
        self.defined_fonts_info[font_nr] = {
            'font_info': font_info,
            'define_instruction': define_font_nr_instr
        }

    def _define_font(self, define_font_nr_instr):
        self.mundane_instructions.append(define_font_nr_instr)

    def select_font(self, font_nr):
        inst = get_select_font_nr_instruction(font_nr)
        self.mundane_instructions.append(inst)
        # TODO: Could actually get this from instructions dynamically.
        self.current_font_nr = font_nr

    @property
    def current_font_info(self):
        return self.defined_fonts_info[self.current_font_nr]['font_info']

    def _end_document(self):
        self._do_postamble()
        # Define all defined fonts again, as required.
        for font_nr, font_details in self.defined_fonts_info.items():
            self._define_font(font_details['define_instruction'])
        self._do_post_postamble()

    def _do_postamble(self):
        # I am told these are often ignored, so leave them un-implemented for
        # now.
        max_page_height_plus_depth = 1
        max_page_width = 1
        post = get_postamble_instruction(self.last_begin_page_pointer,
                                         numerator,
                                         denominator,
                                         self.magnification,
                                         max_page_height_plus_depth,
                                         max_page_width,
                                         self.max_stack_depth,
                                         self.nr_begin_page_pointers
                                         )
        self.mundane_instructions.append(post)

    def _do_post_postamble(self):
        postamble_pointers = self.op_code_pointers(OpCode.postamble)
        assert len(postamble_pointers) == 1
        postamble_pointer = postamble_pointers[-1]

        post_post = get_post_postamble_instruction(postamble_pointer,
                                                   dvi_format)
        self.mundane_instructions.append(post_post)

    def push(self):
        # House-keeping to track maximum stack depth for postamble.
        self.stack_depth += 1
        self.max_stack_depth = max(self.stack_depth, self.max_stack_depth)
        self.mundane_instructions.append(get_push_instruction())

    def pop(self):
        self.stack_depth -= 1
        self.mundane_instructions.append(get_pop_instruction())

    def down(self, a):
        self.mundane_instructions.append(get_down_instruction(a))

    def right(self, a):
        self.mundane_instructions.append(get_right_instruction(a))

    def _encode(self):
        return b''.join(inst.encode() for inst in self.instructions)

    def set_char(self, char):
        self.mundane_instructions.append(get_set_char_instruction(char))

    def put_char(self, char):
        self.mundane_instructions.append(get_put_char_instruction(char))

    def pretty_print(self):
        """Print document instructions in a human-readable manner."""

        def bps(bp):
            """Format a byte pointer."""
            return f'@{bp:3n}: '

        def bls(nb):
            """Format a byte length."""
            return f'[{nb:3n} bytes]'

        # Byte pointer (index of byte number in document).
        bp = 0
        # A gap.
        g = '    '
        # Count boring instructions to be skipped
        boring_count = 0
        boredom_thresh = 3
        for instr in self.instructions:
            # Skip repeated boring instructions that will happen a lot, like
            # putting characters, moving right, and defining fonts (at the
            # start and end).
            if instr.op_code in (OpCode.right_3_byte, OpCode.put_1_byte_char,
                                 OpCode.define_1_byte_font_nr):
                boring_count += 1
            else:
                if boring_count > 0:
                    print('^...^...^...^...^...^...^...^...^...^...^...^...^...^...^')
                boring_count = 0
            if boring_count > boredom_thresh:
                if boring_count == boredom_thresh + 1:
                    print('v...v...v...v...v...v...v...v...v...v...v...v...v...v...v')
                continue

            # Summary of whole instruction.
            print(f'{bps(bp)}: {instr.op_code} {g}{bls(instr.nr_bytes())}')
            print('--------------------------------------------------------')

            # Op-code part of instruction.
            print(f'{bps(bp)}: {g}{instr.encoded_op_code.value:<10n}{g}{g}{bls(instr.encoded_op_code.nr_bytes())} ({instr.op_code})')
            # Track byte number index.
            bp += instr.encoded_op_code.nr_bytes()

            # Arguments part of instruction.
            print('(')
            for arg in instr.arguments:
                if isinstance(arg, EncodedInteger):
                    # If metadata suggests this integer represents a character,
                    # show its character representation as well as the number.
                    if arg.name == 'char':
                        v = f"{arg.value:<4n} ('{chr(arg.value)}')"
                    else:
                        v = f'{arg.value:<10n}'
                    print(f'{bps(bp)}: {g}{v}{g}{g}{bls(arg.nr_bytes())} ({arg.name})')
                # String arguments
                elif isinstance(arg, EncodedString):
                    s = f'"{arg.value}"'
                    d = 10
                    s += ' ' * max(d - len(s), 0)
                    print(f'{bps(bp)}: {g}{s}{g}{g}{bls(arg.nr_bytes())} ({arg.name})')
                # Track byte number index.
                bp += arg.nr_bytes()
            print(')')

    def write(self, stream):
        self._end_page()
        self._end_document()

        # Allow passing a filename.
        if isinstance(stream, str):
            stream = open(stream, 'wb')
        stream.write(self._encode())

    def put_rule(self, height, width):
        inst = get_put_rule_instruction(height, width)
        self.mundane_instructions.append(inst)

    def set_rule(self, height, width):
        inst = get_set_rule_instruction(height, width)
        self.mundane_instructions.append(inst)
