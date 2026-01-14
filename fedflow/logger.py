import logging
from importlib.metadata import version



def setup_logging(logfile: str = "output.log") -> logging.Logger:
    """
    Create generic logger for this project

    :param logfile: file to write the logs to, defaults to "output.log"
    :return: logging.Logger instance
    """
    # make sure the file exists and is empty
    with open(logfile, 'w'):
        pass
    logger = logging.getLogger("fedflow")
    logger.setLevel(logging.INFO)
    fmt = '%(asctime)s %(message)s'
    logger.handlers.clear()
    
    # Console handler
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter(fmt))
    # File handler
    fh = logging.FileHandler(logfile, mode="w")
    fh.setFormatter(logging.Formatter(fmt))
    # selection of logging mode
    sh.setLevel(logging.INFO)
    fh.setLevel(logging.INFO)
    # attach the handlers to the logger
    logger.addHandler(sh)
    logger.addHandler(fh)
    # first entry
    logger.info(f"fedflow {version('fedflow')}")
    return logger


logger = logging.getLogger("fedflow")


def log(msg: str, level = logging.INFO):
    """
    Fallback logging. If handlers are set, 
    send message to logger, otherwise just print

    :param msg: log message
    :param level: log level, defaults to logging.INFO
    """
    if logger.handlers:
        logger.log(level, msg)
    else:
        print(msg)

