import colorama

from .feedback import strep, csep
from .constants.instructions import Instructions, unexpanded_cs_instructions
from .constants.parameters import is_parameter_instr
from .constants.commands import Commands
from .utils import get_unique_id
from .glog import DAGLog

colorama.init()


def get_position_str(chars, char_nr, char_len, line_nr, col_nr):
    here_i = char_nr
    context_len = 60

    before_i = max(here_i - context_len, 0)
    pre_context = ''.join(chars[before_i:here_i])
    if '\n' in pre_context:
        pre_context = pre_context[pre_context.rfind('\n'):]
    else:
        if before_i > 0:
            pre_context = '…' + pre_context

    if char_len is None:
        here_len = 1
    else:
        here_len = char_len
    here_i_end = here_i + here_len
    here = ''.join(chars[here_i:here_i_end])
    here = colorama.Fore.RED + here + colorama.Style.RESET_ALL

    end_i = min(here_i_end + context_len, len(chars))

    post_context = ''.join(chars[here_i_end:end_i])
    if '\n' in post_context:
        post_context = post_context[:post_context.find('\n') + 1]
    else:
        if end_i != len(chars):
            post_context = post_context + '…'

    s = pre_context + here + post_context
    s = strep(s)
    intro = f'{line_nr}:{col_nr}\t'
    return intro + s


class BaseToken:

    def __init__(self, type_, value=None):
        self._type = type_
        self.value = value
        self.slug = get_unique_id()[:6]

    def __hash__(self):
        return hash(self.slug)

    @property
    def type(self):
        return self._type

    @property
    def value_str(self):
        if self.value is None:
            return ''
        elif isinstance(self.value, dict):
            v = self.value.copy()
            if 'lex_type' in v:
                v.pop('lex_type')
            if len(str(v)) > 130:
                return str({
                    k: '...' if k not in ['name'] else val
                    for k, val in v.items()
                })
            else:
                return str(v)
        else:
            return str(self.value)

    @property
    def label_str(self):
        return str(self)

    def __repr__(self):
        return f'{self.__class__.__name__}::{self.type}({self.value_str})'

    def __str__(self):
        vs = self.value_str
        if vs:
            s = f'({vs})'
        else:
            s = ''
        return f'{self.type}{s}'


class AncestryToken(BaseToken):

    def __init__(self, type_, value, parents):
        super().__init__(type_=type_, value=value)
        if parents is not None:
            for p in parents:
                if p is not None and not isinstance(p, BaseToken):
                    raise ValueError(f"A token's parent must be another "
                                     f"token, not '{p}'")
            parents = [p for p in parents if p is not None]
        self.parents = parents

    def print_debug_info(self, state):
        self_dict = self.to_dict()
        log = DAGLog()
        log.write(childs=self_dict, target_node=self)
        print(log.to_str(2))
        self.print_used_macros(state)

    def print_used_macros(self, state):
        macros = self.get_used_macros()
        if macros:
            s = f"Using {len(macros)} macros:"
            print(s)
            print('=' * (len(s) - 1))
            print()
            for macro in macros:
                print(f'\\{macro}:')
                macro_def = state.router.lookup_canonical_control_sequence(macro)
                macro_def_dict = macro_def.to_dict()
                log = DAGLog()
                log.write(childs=macro_def_dict, target_node=macro_def)
                print(log.to_str(1))
                print()

    def get_used_macros(self):
        macros_all = set()
        if self.parents is not None:
            for p in self.parents:
                if isinstance(p, AncestryToken):
                    macros_all.update(p.get_used_macros())
        return macros_all

    def to_dict(self):
        if self.parents is None or not self.parents:
            return None
        d = {}
        for p in self.parents:
            if p is None:
                import pdb; pdb.set_trace()
            if isinstance(p, AncestryToken):
                d[p] = p.to_dict()
            else:
                d[p] = None
        return d


simple_instructions = (
    Instructions.insert,
    Instructions.left_brace,
    Instructions.right_brace,
)


class InstructionToken(AncestryToken):

    def __init__(self, instruction: Instructions, *args, **kwargs) -> None:
        super().__init__(type_=None, *args, **kwargs)
        self.instruction = instruction

    def copy(self, *args, **kwargs):
        v = self.value
        if v is None:
            v_copy = v
        elif isinstance(v, dict):
            v_copy = v.copy()
        elif isinstance(v, int):
            v_copy = v
        else:
            raise Exception
        return self.__class__(instruction=self.instruction,
                              value=v_copy, *args, **kwargs)

    @property
    def type(self):
        return self.instruction.value

    def __repr__(self):
        a = [f'I={self.instruction.name}']
        a.append(f'v={self.value_str}')
        return f'IT({csep(a)})'

    def __str__(self):
        a = []
        a.append(f'{self.value_str}')
        return f'{self.instruction.name}({csep(a, str_func=str)})'

    @property
    def label_str(self):
        if is_parameter_instr(self.instruction):
            return self.value['parameter'].name
        elif self.instruction == Instructions.macro:
            return f"Macro \\{self.value['name']}"
        elif self.instruction in unexpanded_cs_instructions:
            return f"Call \\{self.value['name']}"
        elif self.instruction in simple_instructions:
            return f"Instr {self.instruction.name}"
        else:
            return super().label_str

    def get_used_macros(self):
        macros = super().get_used_macros()
        if self.instruction == Instructions.macro:
            macros.add(self.value['name'])
        return macros


class BuiltToken(AncestryToken):
    pass


class CommandToken(BuiltToken):

    def __init__(self, command: Commands, *args, **kwargs) -> None:
        super().__init__(type_=None, *args, **kwargs)
        self.command = command

    def __repr__(self):
        a = [f'C={self.command.name}']
        a.append(f'v={self.value_str}')
        return f'CT({csep(a)})'

    def __str__(self):
        a = []
        a.append(f'{self.value_str}')
        return f'{self.command.name}({csep(a, str_func=str)})'
