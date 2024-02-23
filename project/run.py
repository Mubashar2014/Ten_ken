"""
Following file is used to start the application
"""

from project import create_app, config

application = create_app()


if __name__ == '__main__':
    application.run(host="127.0.0.1", port=5000, debug=True, load_dotenv=config)
