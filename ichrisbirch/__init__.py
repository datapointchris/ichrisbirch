import logging

from ichrisbirch.logger import initialize_logging

initialize_logging()

logger = logging.getLogger(__name__ + '.__init__')
logger.info('Initialized ichrisbirch package')
logger.info('Initialized root logger')
