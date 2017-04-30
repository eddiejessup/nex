from ..special_quantities import special_quantity_types
from ..tex_parameters import parameter_types
from ..constants.primitive_control_sequences import terminal_primitive_control_sequences_map
from ..constants.literals import literal_types
from ..constants.strange_types import (composite_terminal_token_types,
                                       unexpanded_cs_types,
                                       let_target_type,
                                       def_token_types)


# TODO: Move some tokens to only be in command parser
terminal_types = tuple(terminal_primitive_control_sequences_map.values())
terminal_types += def_token_types
terminal_types += tuple(literal_types)
terminal_types += tuple(unexpanded_cs_types)
terminal_types += (let_target_type,)
terminal_types += tuple(composite_terminal_token_types)
# Remove duplicate types.
terminal_types = tuple(set(terminal_types))

terminal_types += parameter_types
terminal_types += special_quantity_types
