"""App Entry Point"""
import platform
from euphoria import create_app

app = create_app()

if __name__ == '__main__':
    if platform.system() == 'Darwin':
        # Mac
        app.run(port=4200, host='0.0.0.0')
    else:
        # Linux Box
        app.run(port=8200)
