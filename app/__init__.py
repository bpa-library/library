# from flask import Flask

# app = Flask(__name__)

# @app.route('/')
# def home():
#     return "Audio Book Portal - Hello World!"



from app import app as application  # Required for Gunicorn

if __name__ == "__main__":
    application.run()