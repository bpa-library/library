#wsgi_handler.py
from app import app
# from serverless_wsgi import handle_request
# from flask import Flask

application = app

def handler(event, context):
    # from serverless_wsgi import handle_request
    return handle_request(application, event, context)


