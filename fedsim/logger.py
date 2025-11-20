import logging
from importlib.metadata import version



def setup_logging(logfile: str = "output.log", mode: str = "debug") -> logging.Logger:
    """
    Create generic logger for this project

    :param logfile: file to write the logs to, defaults to "output.log"
    :param mode: logging mode, either "debug" or "quiet", defaults to "debug"
    :raises ValueError: if non-existent mode is chosen
    :return: logging.Logger instance
    """
    # make sure the file exists and is empty
    with open(logfile, 'w'):
        pass
    logger = logging.getLogger("fedsim")
    logger.setLevel(logging.DEBUG)
    fmt = '%(asctime)s %(message)s'
    logger.handlers.clear()
    
    # Console handler
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter(fmt))
    # File handler
    fh = logging.FileHandler(logfile, mode="w")
    fh.setFormatter(logging.Formatter(fmt))
    # selection of logging mode
    if mode == "debug":
        sh.setLevel(logging.DEBUG)
        fh.setLevel(logging.DEBUG)
    elif mode == "quiet":
        sh.setLevel(logging.INFO)
        fh.setLevel(logging.INFO)
    else:
        raise ValueError("mode must be 'debug' or 'quiet'")
    # attach the handlers to the logger
    logger.addHandler(sh)
    logger.addHandler(fh)
    # first entry
    logger.info(f"fedsim {version('fedsim')}")
    return logger


logger = logging.getLogger("fedsim")


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

