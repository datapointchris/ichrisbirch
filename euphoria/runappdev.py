import uvicorn
import os

os.environ['ENVIRONMENT'] = 'development'
os.environ['FLASK_DEBUG'] = 'development'

if __name__ == '__main__':
    # import here in order to set the environment variables first
    from backend.app.main import create_app
    app = create_app()
    app.run(host='127.0.0.1', port=6000, debug=True)
    # uvicorn.run(app, port=6400, log_level="debug")
