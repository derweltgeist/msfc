class InvalidCLIArgument(Exception):
    """Used for invalid CLI argument."""
    pass

class InvalidOrMissingConfig(Exception):
    """Used for invalid configurations."""
    pass

class InvalidDate(Exception):
    """Used for invalid usage of date."""
    pass

class InvalidDateIndex(Exception):
    """Used for internal error of show() of database.py where you use invalid index."""
    pass

class InvalidDatabaseShowFlags(Exception):
    """Used for invalid flags format of run.py database show."""
    pass

class InvalidValueFlagsFormat(Exception):
    """Used for invalid formats of value flags."""
    pass

class InvalidDatabaseError(Exception):
    """Used for invalid database."""
    pass

class InvalidSheetFilePath(Exception):
    """Used for invalid sheet path."""
    pass

class InvalidSheetContent(Exception):
    """Used for invalid sheet content."""
    pass

class InvalidGetArg(Exception):
    """Used for invalid arg of get, internal."""
    pass

class InvalidControlGraph(Exception):
    """Used for invalid --graph of control graph"""
    pass

