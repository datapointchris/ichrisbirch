"""App Entry Point"""
import platform
import os

os.environ['ENVIRONMENT'] = os.environ['FLASK_ENV'] = 'development'

if __name__ == '__main__':
    from backend.app.main import create_app

    app = create_app()
    if platform.system() == 'Darwin':
        # Mac
        app.run(port=4200, host='0.0.0.0')
    else:
        # Linux Box
        app.run(port=8200)
