import streamlit as st
import requests

# Connect to your Flask API
API_URL = "https://library-11.vercel.app/"

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