# import streamlit_app.auth
# import streamlit_app.main

# streamlit_app/__init__.py
"""
Audio Library Streamlit Application
----------------------------------
Main package for the audio library web application.
"""

# Version of the application
__version__ = "1.0.0"

# Import main modules to make them easily accessible
from . import auth
from . import main
from . import config

# Optional: Import user subpackage
from . import user

# Export commonly used functions and classes
__all__ = [
    'auth',
    'main', 
    'config',
    'user'
]

# Package initialization code (if needed)
def initialize_app():
    """Initialize the application with default settings"""
    print(f"Audio Library App v{__version__} initialized")