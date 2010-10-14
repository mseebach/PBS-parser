
def assertEquals(reason, expected, actual):
    if actual != expected:
        raise PBSParseException("{reason}. Expected {expected}, but got {actual}"
                                .format(reason=reason,
                                        expected=extected,
                                        actual=actual))
