from records import PBSParseException

def assertEquals(reason, expected, actual):
    if actual != expected:
        raise PBSParseException("{reason}. Expected {expected}, but got {actual}"
                                .format(reason=reason,
                                        expected=expected,
                                        actual=actual))
