from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Audio Book Portal - Hello World!"

# Vercel requires this WSGI entry point
application = app
