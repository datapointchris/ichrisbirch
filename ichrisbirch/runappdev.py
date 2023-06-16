from ichrisbirch.logger import create_base_logger
from ichrisbirch.wsgi import app

if __name__ == '__main__':
    logger = create_base_logger()
    app.run(host='127.0.0.1', port=6200, debug=True)
