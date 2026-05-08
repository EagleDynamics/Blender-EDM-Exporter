# Can be caugh, export can be continued.
class EdmException(Exception):
    pass

# Export failed, no model generated.
class EdmFatalException(Exception):
    pass
