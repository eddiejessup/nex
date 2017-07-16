import logging
from collections import deque

from ..tokens import BuiltToken
from ..utils import LogicError
from ..router import NoSuchControlSequence
from ..constants.instructions import Instructions

logger = logging.getLogger(__name__)

# Stuff specific to *my parsing*.

letter_to_non_active_uncased_type_map = {
    #  For hex characters, need to look for the composite production, not the
    #  terminal production, because could be, for example, 'A' or
    #  'NON_ACTIVE_UNCASED_A', so we should look for the composite production,
    #  'non_active_uncased_a'.
    'A': 'non_active_uncased_a',
    'B': 'non_active_uncased_b',
    'C': 'non_active_uncased_c',
    'D': 'non_active_uncased_d',
    'E': 'non_active_uncased_e',
    'F': 'non_active_uncased_f',
    'a': Instructions.non_active_uncased_a.value,
    'b': Instructions.non_active_uncased_b.value,
    'c': Instructions.non_active_uncased_c.value,
    'd': Instructions.non_active_uncased_d.value,
    'e': Instructions.non_active_uncased_e.value,
    'f': Instructions.non_active_uncased_f.value,
    'g': Instructions.non_active_uncased_g.value,
    'h': Instructions.non_active_uncased_h.value,
    'i': Instructions.non_active_uncased_i.value,
    'j': Instructions.non_active_uncased_j.value,
    'k': Instructions.non_active_uncased_k.value,
    'l': Instructions.non_active_uncased_l.value,
    'm': Instructions.non_active_uncased_m.value,
    'n': Instructions.non_active_uncased_n.value,
    'o': Instructions.non_active_uncased_o.value,
    'p': Instructions.non_active_uncased_p.value,
    'q': Instructions.non_active_uncased_q.value,
    'r': Instructions.non_active_uncased_r.value,
    's': Instructions.non_active_uncased_s.value,
    't': Instructions.non_active_uncased_t.value,
    'u': Instructions.non_active_uncased_u.value,
    'v': Instructions.non_active_uncased_v.value,
    'w': Instructions.non_active_uncased_w.value,
    'x': Instructions.non_active_uncased_x.value,
    'y': Instructions.non_active_uncased_y.value,
    'z': Instructions.non_active_uncased_z.value,
    'G': Instructions.non_active_uncased_g.value,
    'H': Instructions.non_active_uncased_h.value,
    'I': Instructions.non_active_uncased_i.value,
    'J': Instructions.non_active_uncased_j.value,
    'K': Instructions.non_active_uncased_k.value,
    'L': Instructions.non_active_uncased_l.value,
    'M': Instructions.non_active_uncased_m.value,
    'N': Instructions.non_active_uncased_n.value,
    'O': Instructions.non_active_uncased_o.value,
    'P': Instructions.non_active_uncased_p.value,
    'Q': Instructions.non_active_uncased_q.value,
    'R': Instructions.non_active_uncased_r.value,
    'S': Instructions.non_active_uncased_s.value,
    'T': Instructions.non_active_uncased_t.value,
    'U': Instructions.non_active_uncased_u.value,
    'V': Instructions.non_active_uncased_v.value,
    'W': Instructions.non_active_uncased_w.value,
    'X': Instructions.non_active_uncased_x.value,
    'Y': Instructions.non_active_uncased_y.value,
    'Z': Instructions.non_active_uncased_z.value,
}


def make_literal_token(p):
    s = ''.join(t.value['char'] for t in p)
    return BuiltToken(type_='literal', value=s, position_like=p)


def str_to_char_types(s):
    return (letter_to_non_active_uncased_type_map[c] for c in s)


def get_literal_production_rule(word, target=None):
    if target is None:
        target = word
    rule = ' '.join(str_to_char_types(word))
    return '{} : {}'.format(target, rule)


class DigitCollection:

    def __init__(self, base):
        self.base = base
        self.digits = []

    def __repr__(self):
        return f'{self.__class__.__name__}(base {self.base}: {self.digits})'


# More generic utilities.

def wrap(pg, func, rule):
    f = pg.production(rule)
    return f(func)


class ParsingSyntaxError(Exception):
    pass


class ExhaustedTokensError(Exception):
    pass


end_tag = '$end'


def is_end_token(t):
    return t.type == end_tag and t.value == end_tag


class GetBuffer:

    def __init__(self, getter, initial=None):
        self.queue = deque()
        if initial is not None:
            self.queue.extend(initial)
        self.getter = getter

    def __iter__(self):
        return self

    def __next__(self):
        while not self.queue:
            self.queue.extend(self.getter())
        return self.queue.popleft()


def chunk_iter(banisher, parser):
    """
    Return an iterator over sequential chunks, each satisfying the objective of
    a `parser`, by collecting input tokens from `banisher`.
    """
    while True:
        yield get_chunk(banisher, parser)


def get_chunk(banisher, parser, initial=None):
    """
    Return a chunk satisfying the objective of a `parser`, by collecting input
    tokens from `banisher`.
    """
    # Processing input tokens might return many tokens, so store them in a
    # buffer.
    input_buffer = GetBuffer(getter=banisher.get_next_output_list,
                             initial=initial)

    # Get the actual chunk.
    chunk, parse_queue = _get_chunk(input_buffer, parser)

    # We might want to reverse the composition of terminal tokens we just
    # did in the parser, so save the bits in a special place.
    chunk._terminal_tokens = list(parse_queue)

    # Replace any tokens left in the buffer onto the banisher's queue.
    if input_buffer.queue:
        logger.info(f"Cleaning up tokens on chunk grabber's buffer: {input_buffer.queue}")
        banisher.replace_tokens_on_input(input_buffer.queue)
    return chunk


def _get_chunk(input_queue, parser):
    """
    Return a chunk satisfying the objective of a `parser`, by collecting input
    tokens from `input_queue`.
    """
    # Get enough tokens to grab a parse-chunk. We know to stop adding tokens
    # when we see a switch from failing because we run out of tokens
    # (ExhaustedTokensError) to an actual syntax error (ParsingSyntaxError).
    # Want to extend the queue-to-be-parsed one token at a time,
    # so we can break as soon as we have all we need.
    parse_queue = deque()
    # We keep track of if we have parsed, just for checking for weird
    # situations.
    have_parsed = False
    while True:
        try:
            chunk = parser.parse(iter(parse_queue))
        # If we got a syntax error, this should mean we have spilled over
        # into parsing the next chunk.
        except ParsingSyntaxError as exc:
            # If we have already parsed a chunk, then we use this as our
            # result.
            if have_parsed:
                # We got one token of fluff due to extra read, to make the
                # parse queue not-parse. So put it back on the buffer.
                fluff_tok = parse_queue.pop()
                logger.debug(f'Replacing fluff token {fluff_tok} on to-parse queue.')
                input_queue.queue.appendleft(fluff_tok)
                logger.info(f'Got chunk "{chunk}", through failed parsing')
                return chunk, parse_queue
            # If we have not yet parsed, then something is wrong.
            else:
                exc.args += (f'Tokens: {list(parse_queue)}',)
                raise
        except ExhaustedTokensError:
            # Carry on getting more tokens, because it seems we can.
            pass
        else:
            # In our modified version of rply, we annotate the
            # output token to indicate whether the only action from the
            # current parse state could be to end. In this case, we do not
            # bother adding another token, and just return the chunk.
            # This reduces the number of cases where we expand too far, and
            # must handle bad handling of the post-chunk tokens caused by
            # not acting on this chunk.
            if chunk._could_only_end:
                logger.info(f'Got chunk "{chunk}", through inevitability')
                return chunk, parse_queue
            have_parsed = True

        try:
            t = next(input_queue)
        except EOFError:
            # If we get an EOFError, and we have just started trying to
            # get a parse-chunk, we are done, so just propagate the
            # exception to wrap things up.
            if not parse_queue:
                raise
            # If we get an EOFError and we have already parsed, we need to
            # return this parse-chunk, then next time round we will be
            # done.
            elif have_parsed:
                logger.info(f'Got chunk "{chunk}", through end-of-file')
                return chunk, parse_queue
            # If we get to the end of the file and we have a chunk queue
            # that can't be parsed, something is wrong.
            else:
                raise ValueError(f'Got to end-of-file but still have '
                                 f'unparsed tokens: {parse_queue}')
        # If we get an expansion error, it might be because we need to
        # act on the chunk we have so far first.
        except NoSuchControlSequence as e:
            # This is only possible if we have already parsed the chunk-so-
            # far.
            if have_parsed:
                # This might always be fine, but log it anyway.
                logger.warning('Ignoring failed expansion in chunk grabber')
                logger.info(f'Got chunk "{chunk}", through failed expansion')
                return chunk, parse_queue
            # Otherwise, indeed something is wrong.
            else:
                raise
        parse_queue.append(t)
    raise LogicError('Broke from command parsing loop unexpectedly')
