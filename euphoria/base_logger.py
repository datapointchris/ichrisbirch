import logging


formatter = logging.Formatter("%(asctime)s | %(name)s:%(lineno)d | %(levelname)s: %(message)s")
log_location = '/usr/local/var/log/ichrisbirch/log.log'

ch = logging.StreamHandler()
ch.setFormatter(formatter)

fh = logging.FileHandler(filename=log_location)
fh.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(ch)
logger.addHandler(fh)
logger.debug(f'Log Location: {log_location}')

logging.getLogger('matplotlib').setLevel(logging.INFO)
