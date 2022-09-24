"""App Entry Point"""
import os

os.environ['ENVIRONMENT'] = os.environ['FLASK_DEBUG'] = 'development'

if __name__ == '__main__':
    from backend.app.main import create_app
    app = create_app()
    app.run(host='0.0.0.0', port=4000)
