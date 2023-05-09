from ichrisbirch import base_logger
from ichrisbirch.config import get_settings
from ichrisbirch.wsgi import app

if __name__ == '__main__':
    base_logger.init(get_settings())
    app.run(host='127.0.0.1', port=6400, debug=True)
