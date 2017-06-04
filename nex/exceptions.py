class LogicError(Exception):
    """Got into situations that should not be internally possible."""
    pass


class UserError(Exception):
    """The input from the user is incorrect."""
    pass
