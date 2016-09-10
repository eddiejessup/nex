class ExpectedParsingError(Exception):
    pass


class ExhaustedTokensError(Exception):
    pass


def is_end_token(t):
    end_tag = '$end'
    return (hasattr(t, 'name') and
            all(a == end_tag for a in (t.name, t.value)))
