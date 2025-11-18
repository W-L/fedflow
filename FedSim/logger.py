import logging



def setup_logging(logfile="output.log", mode="debug"):
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


    if mode == "debug":
        sh.setLevel(logging.DEBUG)
        fh.setLevel(logging.DEBUG)
    elif mode == "quiet":
        sh.setLevel(logging.INFO)
        fh.setLevel(logging.INFO)
    else:
        raise ValueError("mode must be 'debug' or 'quiet'")

    logger.addHandler(sh)
    logger.addHandler(fh)

    logger.info("FedSim v0.1")
    return logger


logger = logging.getLogger("fedsim")


def log(msg, level=logging.INFO):
    """
    Fallback-safe logging:
    - If logger is configured → send to logger
    - If not → print()
    """
    if logger.handlers:
        logger.log(level, msg)
    else:
        print(msg)

