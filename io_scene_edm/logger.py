from pyedm_platform_selector import pyedm
from edm_exception import EdmFatalException, EdmException

class LogCtx:
    
    obj: any = None
    action: any = None
    
    def __init__(self, obj = None, action = None) -> None:
        self.obj = obj
        self.action = action

    def __str__(self):
        out = ''
        if self.obj:
            out += f'Obj: {self.obj.name}, '
        if self.action:
            out += f'Action: {self.action}, '

        if not out:
            return out
        
        return out[:-2] + ' | '

LOG_CTX = None

class Logger:

    def __init__(self) -> None:
        self.errors = []
        self.warnings = []

    def reset(self):
        self.errors = []
        self.warnings = []

    def fatal(self, msg):
        emsg = f'{LOG_CTX if LOG_CTX else ""}{msg}'
        self.errors.append(emsg)
        pyedm.log_error(emsg)
        raise EdmFatalException(emsg)

    def error(self, msg):
        emsg = f'{LOG_CTX if LOG_CTX else ""}{msg}'
        self.errors.append(emsg)
        pyedm.log_error(emsg)
#        raise EdmException(emsg)

    def warning(self, msg, verbosity_level = 0):
        emsg = f'{LOG_CTX if LOG_CTX else ""}{msg}'
        pyedm.log_warning(emsg)

    def info(self, msg, verbosity_level = 0):
        emsg = f'{LOG_CTX if LOG_CTX else ""}{msg}'
        pyedm.log_info(emsg)

    def debug(self, msg):
        emsg = f'{LOG_CTX if LOG_CTX else ""}{msg}'
        pyedm.log_debug(emsg)

log = Logger()