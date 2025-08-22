import streamlit as st
import requests
import jwt
from datetime import datetime, timedelta

API_URL = "https://library-11.vercel.app"  # Your Flask API

def login_user(email, password):
    try:
        response = requests.post(f"{API_URL}/api/login", json={
            "email": email,
            "password": password
        })
        return response.json() if response.status_code == 200 else None
    except:
        return None

def register_user(name, email, password, membership_number=None):
    try:
        response = requests.post(f"{API_URL}/api/register", json={
            "name": name,
            "email": email,
            "password": password,
            "membership_number": membership_number
        })
        return response.json()
    except:
        return {"error": "Connection failed"}

# ... rest of your Streamlit code unchanged ...


st.title("📚 Audio Book Library")
st.subheader("Browse Available Books")

# Fetch data from Flask API
response = requests.get(f"{API_URL}/")
if response.status_code == 200:
    books = response.json().get("books", [])
    for book in books:
        with st.expander(book['title']):
            st.write(f"ID: {book['id']}")
            st.audio(f"https://your-b2-url/{book['id']}.mp3")  # Backblaze URL
else:
    st.error("Failed to load books from database")