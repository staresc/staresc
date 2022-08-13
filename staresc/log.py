import logging

VULN    = logging.INFO + 1
DEFAULT = 1000

SEVERITY2COLOR = {
    "critical" : "\033[0;35m", # purple
    "high"     : "\033[0;31m", # red
    "medium"   : "\033[1;33m", # yellow
    "low"      : "\033[0;36m", # cyan
    "info"     : "\033[0;32m", # green
}

class StarescLogger:

    LEVEL_TO_STRING = {
        VULN      : "VULN",
    }

    logger: logging.Logger

    class StarescLoggingFormatter(logging.Formatter):

        FORMATS = {
            DEFAULT : '[STARESC]:[%(target)s]:[%(levelname)s]: %(message)s',
            VULN    : '[FINDING]:[%(target)s]:[%(c)s%(severity)s%(r)s]:[%(c)s%(plugin)s%(r)s]'
        }

        def format(self, record):  
            f = self.FORMATS.get(record.levelno, self.FORMATS[DEFAULT])
            formatter = logging.Formatter(fmt=f)
            return formatter.format(record)


    # This function is taken from: https://stackoverflow.com/a/35804945
    @staticmethod
    def __add_logging_level(levelName, levelNum, methodName=None):
        if not methodName:
            methodName = levelName.lower()

        if hasattr(logging, levelName):
            raise AttributeError(f'{levelName} already defined in logging module')
        if hasattr(logging, methodName):
            raise AttributeError(f'{methodName} already defined in logging module')
        if hasattr(logging.getLoggerClass(), methodName):
            raise AttributeError(f'{methodName} already defined in logger class')

        def logForLevel(self, message, *args, **kwargs):
            if self.isEnabledFor(levelNum):
                self._log(levelNum, message, args, **kwargs)
        def logToRoot(message, *args, **kwargs):
            logging.log(levelNum, message, *args, **kwargs)

        logging.addLevelName(levelNum, levelName)
        setattr(logging, levelName, levelNum)
        setattr(logging.getLoggerClass(), methodName, logForLevel)
        setattr(logging, methodName, logToRoot)


    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        try:
            # Initialize all levels in root logger
            for lev, name in self.LEVEL_TO_STRING.items():
                self.__add_logging_level(name, lev)

        except AttributeError:
            # If attribute error: logger already configured
            # so we can skip this step
            return
            
        hdlr = logging.StreamHandler()
        hdlr.setFormatter(self.StarescLoggingFormatter())
        self.logger.addHandler(hdlr)


    def setLevelInfo(self):
        self.logger.setLevel(logging.INFO)

    
    def setLevelDebug(self):
        self.logger.setLevel(logging.DEBUG)


    def info(self, msg: str, target:str = None):
        self.logger.info(msg, extra={"target": target})

    
    def debug(self, msg: str, target:str = None):
        self.logger.debug(msg, extra={"target": target})

    
    def error(self, msg: str, target:str = None):
        self.logger.error(msg, extra={"target": target})


    def print_vuln(self, host: str, port: int, severity: str, plugin_name: str):
        e = {
            "target"   : f"{host}:{port}",
            "severity" : severity,
            "plugin"   : plugin_name,
            "c"        : SEVERITY2COLOR.get(severity.lower(), ""),
            "r"        : "\033[0m",
        }
        self.logger.vuln("", extra=e)
       