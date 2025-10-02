# streamlit_app/config.py
#########################
import os
from dotenv import load_dotenv
import streamlit as st
from flask import Flask, jsonify, request


load_dotenv()

try:
    # Streamlit Cloud secrets
    API_URL = st.secrets["API_URL"]
    DEBUG = st.secrets.get("DEBUG", "False").lower() == "true"
    ENVIRONMENT = st.secrets.get("ENVIRONMENT", "production")
except (KeyError, AttributeError):
    # Fallback to .env file for local development
    load_dotenv()
    API_URL = os.getenv('API_URL', 'http://localhost:8000')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

print(f"✅ Environment: {ENVIRONMENT}")
print(f"✅ API_URL: {API_URL}")
print(f"✅ Debug mode: {DEBUG}")
