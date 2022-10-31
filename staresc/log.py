import logging

from staresc.output import Output

VULN     = logging.INFO + 1
RAW      = logging.INFO + 2
CHECK    = logging.INFO + 3
DEFAULT = 1000

SEVERITY2COLOR = {
    "critical" : "\033[0;35m", # purple
    "high"     : "\033[0;31m", # red
    "medium"   : "\033[1;33m", # yellow
    "low"      : "\033[0;36m", # cyan
    "info"     : "\033[0;32m", # green
}

class Logger:

    LEVEL_TO_STRING = {
        VULN      : "VULN",
        RAW       : "RAW",
        CHECK     : "CHECK",
    }

    logger: logging.Logger
    progress_msg:str = "[STARESC]:[{}]:[RAW]: {}"

    class LoggingFormatter(logging.Formatter):

        FORMATS = {
            DEFAULT : '[STARESC]:[%(asctime)s]:[%(levelname)s]: %(message)s',
            VULN    : '[STARESC]:[%(target)s]:[%(c)s%(severity)s%(r)s]:[%(c)s%(plugin)s%(r)s]',
            RAW     : '[STARESC]:[%(target)s]:[RAW]: %(message)s',
            CHECK   : '[STARESC]:[%(asctime)s]:[CHECK]: %(target)s: %(message)s'
        }

        def format(self, record):  
            f = self.FORMATS.get(record.levelno, self.FORMATS[DEFAULT])
            formatter = logging.Formatter(fmt=f, datefmt='%Y-%m-%d %H:%M:%S')
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
        hdlr.setFormatter(self.LoggingFormatter())
        self.logger.addHandler(hdlr)


    def setLevelInfo(self):
        self.logger.setLevel(logging.INFO)

    
    def setLevelDebug(self):
        self.logger.setLevel(logging.DEBUG)


    def info(self, msg: str):
        self.logger.info(msg)

    
    def debug(self, msg: str):
        self.logger.debug(msg)

    
    def error(self, msg: str):
        self.logger.error(msg)


    def print_if_vuln(self, o: Output):
        if not o.is_vuln_found():
            return

        host = o.target.hostname
        port = o.target.port

        e = {
            "target"   : f"{host}:{port}",
            "severity" : o.plugin.severity,
            "plugin"   : o.plugin.name,
            "c"        : SEVERITY2COLOR.get(o.plugin.severity.lower(), ""),
            "r"        : "\033[0m",
        }

        self.logger.vuln("", extra=e) #type: ignore


    def raw(self, target:str, port:str, msg:str):
        e = {
            "target": f"{target}:{port}",
        }     
        self.logger.raw(msg, extra=e) #type: ignore

    
    def check(self, target:str, msg:str):
        e = {
            "target": target,
        }     
        self.logger.check(msg, extra=e) #type: ignore