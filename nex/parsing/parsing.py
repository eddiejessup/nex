import warnings
import logging

from ..rply.parsergenerator import ParserGenerator

from . import (
    number_rules,
    dimen_rules,
    glue_rules,
    character_rules,
    command_rules,
    condition_rules,
    variable_rules,
    assignment_rules,
)
from .terminals import terminal_types
from .utils import ParsingSyntaxError, ExhaustedTokensError, is_end_token

logger = logging.getLogger(__name__)


pg = ParserGenerator(terminal_types, cache_id="changeme")
command_rules.add_command_rules(pg)
assignment_rules.add_assignment_rules(pg)
condition_rules.add_condition_rules(pg)
variable_rules.add_variable_rules(pg)
glue_rules.add_glue_rules(pg)
dimen_rules.add_dimen_rules(pg)
number_rules.add_number_rules(pg)
character_rules.add_character_rules(pg)


@pg.production('empty :')
def empty(p):
    return None


def chunker_error(look_ahead):
    # If we have exhausted the list of tokens while still
    # having a valid command, we should read more tokens until we get a syntax
    # error.
    if is_end_token(look_ahead):
        raise ExhaustedTokensError
    # Assume we have an actual syntax error, which we interpret to mean the
    # current command has finished being parsed and we are looking at tokens
    # for the next command.
    else:
        raise ParsingSyntaxError(look_ahead)


def batch_error(look_ahead):
    raise ParsingSyntaxError(look_ahead)


def get_parser(start='command', chunking=True):
    """Build and return a parser that tries to construct the `start` token. By
    default this is `command`, the usual target of the program. Other values
    can be passed to get smaller semantic units, for detailed parsing and
    testing."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        parser = pg.build(start=start)
    if chunking:
        error_handler = chunker_error
    else:
        error_handler = batch_error
    parser.error_handler = error_handler
    return parser


command_parser = get_parser()
