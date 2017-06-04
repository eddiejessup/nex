import logging

from .constants.instructions import unexpanded_cs_instructions
from .instructioner import Instructioner
from .reader import EndOfFile
from .utils import NoSuchControlSequence

logger = logging.getLogger(__name__)


class Resolver:

    def __init__(self, instructioner, router):
        self.instructioner = instructioner
        self.router = router

    @classmethod
    def from_string(cls, router, *args, **kwargs):
        instructioner = Instructioner.from_string(*args, **kwargs)
        return cls(instructioner, router=router)

    def replace_tokens_on_input(self, *args, **kwargs):
        self.instructioner.replace_tokens_on_input(*args, **kwargs)

    def iter_unexpanded(self):
        while True:
            yield self.next_unexpanded()

    def next_unexpanded(self):
        return next(self.instructioner)

    def next_expanded(self):
        # If the token is an unexpanded control sequence call, and expansion is
        # not suppressed, then we must resolve the call:
        # - A user control sequence will become a macro instruction token.
        # - A \let character will become its character instruction token.
        # - A primitive control sequence will become its instruction token.
        # NOTE: I've made this mistake twice now: we can't make this resolution
        # into a two-call process, where we resolve the token, put the resolved
        # token on the input, then handle it in the next call. This is because,
        # for example, \expandafter expects a single call to this method to do
        # resolution and actual expansion. Basically this method has certain
        # responsibilites to do a certain amount to a token in each call.
        instr_tok = self.next_unexpanded()
        if instr_tok.instruction in unexpanded_cs_instructions:
            name = instr_tok.value['name']
            try:
                instr_tok = self.router.lookup_control_sequence(
                    name, position_like=instr_tok)
            except NoSuchControlSequence:
                # Might be that we are parsing too far in a chunk, and just
                # need to execute a command before this can be understood. Put
                # the token back on the input, potentially to read again.
                self.replace_tokens_on_input([instr_tok])
                raise
        return instr_tok

    def advance_to_end(self, expand=True):
        while True:
            try:
                if expand:
                    yield self.next_expanded()
                else:
                    yield self.next_unexpanded()
            except EndOfFile:
                return
