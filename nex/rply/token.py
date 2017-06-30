class Token(object):
    """
    Represents a syntactically relevant piece of text.

    :param name: A string describing the kind of text represented.
    :param value: The actual text represented.
    :param source_pos: A :class:`SourcePosition` object representing the
                       position of the first character in the source from which
                       this token was generated.
    """
    def __init__(self, name, value, source_pos=None):
        self.name = name
        self.value = value
        self.source_pos = source_pos

    def __repr__(self):
        return "Token(%r, %r)" % (self.name, self.value)

    def __eq__(self, other):
        if not isinstance(other, Token):
            return NotImplemented
        return self.name == other.name and self.value == other.value

    def gettokentype(self):
        """
        Returns the type or name of the token.
        """
        return self.name

    def getsourcepos(self):
        """
        Returns a :class:`SourcePosition` instance, describing the position of
        this token's first character in the source.
        """
        return self.source_pos

    def getstr(self):
        """
        Returns the string represented by this token.
        """
        return self.value
