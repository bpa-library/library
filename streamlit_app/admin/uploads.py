# streamlit_app/admin/uploads.py
import streamlit as st
import requests
from config import API_URL, DEBUG
# import os
# import base as b
from components.helpers import extract_chapter_number


def upload_audio():
    st.header("📤 Upload Audio Files")
    
    # Book selection
    books = get_all_books()
    if not books:
        st.warning("No books available. Please add a book first.")
        return
    
    book_options = {book['id']: f"{book['title']} by {book['author']}" for book in books}
    selected_book_id = st.selectbox(
        "Select Book", 
        options=list(book_options.keys()),
        format_func=lambda x: book_options[x]
    )
    
    # File upload
    uploaded_files = st.file_uploader(
        "Choose audio files", 
        type=['mp3', 'wav', 'm4a', 'ogg'], 
        accept_multiple_files=True,
        help="Select one or more audio files to upload"
    )
    
    if uploaded_files and st.button("🚀 Upload Files", type="primary"):
        success_count = 0
        total_count = len(uploaded_files)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, file in enumerate(uploaded_files):
            status_text.text(f"Checking {i+1}/{total_count}: {file.name}")
    
            chapter_number = extract_chapter_number(file.name)
            if chapter_number is None:
                st.info(f"⏭️ Skipped non-chapter file: {file.name}")
                continue  # do not upload, do not save in DB

            status_text.text(f"Uploading {i+1}/{total_count}: {file.name}")
            if upload_to_backblaze(file, selected_book_id):
                success_count += 1

            progress_bar.progress((i + 1) / total_count)

            # status_text.text(f"Uploading {i+1}/{total_count}: {file.name}")
            # if upload_to_backblaze(file, selected_book_id):
            #     success_count += 1
            # progress_bar.progress((i + 1) / total_count)
        
        progress_bar.empty()
        status_text.empty()
        
        if success_count == total_count:
            st.success(f"✅ All {success_count} files uploaded successfully!")
        else:
            st.warning(f"⚠️ {success_count} out of {total_count} files uploaded successfully.")
            
        # Show uploaded files
        st.subheader("📋 Uploaded Files")
        chapters = get_book_chapters(selected_book_id)
        for chapter in chapters:
            chapter_num = chapter.get("chapter_number")
            if chapter_num:
                st.write(f"- {chapter['title']} (Chapter {chapter_num})")
            else:
                st.write(f"- {chapter['title']} (Non-chapter audio)")
            # st.write(f"- {chapter['title']} (Chapter {chapter['chapter_number']})")


def get_all_books():
    """Streamlit function to fetch books via API"""
    try:
        response = requests.get(f"{API_URL}/api/get_all_books", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data.get("books", [])
        return []
    except Exception as e:
        print(f"❌ Error fetching books: {e}")
        return []
    

def upload_to_backblaze(file, book_id):
    """Send file to Flask API, which handles upload + DB insert"""
    try:
        files = {"file": (file.name, file, "audio/mpeg")}
        response = requests.post(
            f"{API_URL}/api/upload_audio",
            data={"book_id": book_id},
            files=files,
            timeout=30
        )
        data = response.json()
        if response.status_code == 200 and data.get("success"):
            st.success(f"✅ Uploaded: {file.name}")
            return True
        else:
            st.error(f"❌ Upload failed: {data.get('error')}")
            return False
    except Exception as e:
        st.error(f"❌ API error: {str(e)}")


def get_book_chapters(book_id):
    """Get all chapters for a book via API"""
    try:
        response = requests.get(
            f"{API_URL}/api/chapters",
            params={"book_id": book_id},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('chapters')
        return []
        
    except Exception as e:
        print(f"❌ Error getting book chapters: {str(e)}")
        return []
    

