import logging



def setup_logging(logfile="output.log"):
    with open(logfile, 'w'):
        pass
    logger = logging.getLogger("fedsim")
    logger.setLevel(logging.DEBUG)
    fmt = '%(asctime)s %(message)s'

    if not logger.handlers:  
        # Console handler
        sh = logging.StreamHandler()
        sh.setLevel(logging.DEBUG)
        sh.setFormatter(logging.Formatter(fmt))
        logger.addHandler(sh)
        # File handler
        fh = logging.FileHandler(logfile, mode="w")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(fmt))
        logger.addHandler(fh)

    logger.info("FedSim v0.1")
    return logger


logger = logging.getLogger("fedsim")


def log(msg):
    """
    Fallback-safe logging:
    - If logger is configured → send to logger
    - If not → print()
    """
    if logger.handlers:
        logger.info(msg)
    else:
        print(msg)

