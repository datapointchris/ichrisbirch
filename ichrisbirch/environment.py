import logging
import os

import dotenv

logger = logging.getLogger(__name__)

if environment := os.getenv('ENVIRONMENT'):
    match environment:
        case 'development':
            env_file = dotenv.find_dotenv('.env.dev')
            dotenv.load_dotenv(env_file)
        case 'testing':
            env_file = dotenv.find_dotenv('.env.test')
            dotenv.load_dotenv(env_file)
        case 'production':
            env_file = dotenv.find_dotenv('.env.prod')
            dotenv.load_dotenv(env_file)
        case _:
            logger.error(f'Unrecognized Environment Variable: {environment}')
            raise ValueError(
                f'Unrecognized Environment Variable: {environment}\n'
                'Did you set ENVIRONMENT before starting the program?'
            )

logger.debug(f"Loaded env file: {env_file}")
