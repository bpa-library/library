# streamlit_app/user/browse.py
import streamlit as st
import requests
from config import API_URL, DEBUG 

######## browse_books ########
def browse_books():
    """Main book browsing interface"""
    st.title("📚 Audio Book Library")
    st.subheader("Browse Available Books")
    
    # Search and pagination controls
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_query = st.text_input("🔍 Search books", placeholder="Search by title, author, or category")
    
    with col2:
        page_size = st.selectbox("Books per page", [10, 20, 50, 100], index=0)
    
    try:
        page = st.session_state.get('current_page', 1)
        
        params = {
            'page': page,
            'limit': page_size
        }
        
        if search_query:
            params['search'] = search_query

        response = requests.get(f"{API_URL}/books", params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            books = data.get("books", [])
            pagination = data.get("pagination", {})
            
            # Display results count
            total_books = pagination.get('total', 0)
            if search_query:
                st.write(f"**Found {len(books)} of {total_books} books matching '{search_query}'**")
            else:
                st.write(f"**Displaying {len(books)} of {total_books} total books**")
            
            if books:
                display_books_grid(books, pagination)
            else:
                st.info("No books found matching your search criteria.")
                
        else:
            st.error("Failed to load books from the server")
            
    except Exception as e:
        st.error(f"Error loading books: {str(e)}")


######## browse_books - display_books_grid ########
def display_books_grid(books, pagination):
    """Display books in a grid layout with pagination"""
    for book in books:
        with st.expander(f"📖 {book['title']} by {book.get('author', 'Unknown')}", expanded=False):
            display_book_details(book)
    
    # Pagination controls at the bottom
    display_pagination_controls(pagination)


######## browse_books - display_pagination_controls ########
def display_pagination_controls(pagination):
    """Display pagination controls"""
    current_page = pagination.get('page', 1)
    total_pages = pagination.get('pages', 1)
    
    if total_pages > 1:
        col_prev, col_info, col_next = st.columns([1, 2, 1])
        
        with col_prev:
            if current_page > 1:
                if st.button("⬅️ Previous", use_container_width=True):
                    st.session_state.current_page = current_page - 1
                    st.rerun()
        
        with col_info:
            st.write(f"**Page {current_page} of {total_pages}**")
            # Add page jump for many pages
            if total_pages > 5:
                jump_page = st.number_input("Go to page", min_value=1, max_value=total_pages, value=current_page, key="page_jump")
                if jump_page != current_page:
                    st.session_state.current_page = jump_page
                    st.rerun()
        
        with col_next:
            if current_page < total_pages:
                if st.button("Next ➡️", use_container_width=True):
                    st.session_state.current_page = current_page + 1
                    st.rerun()


######## browse_books - display_book_details ########
def display_book_details(book):
    """Display detailed information about a single book"""
    col_info, col_meta = st.columns([2, 1])
    
    with col_info:
        st.write(f"**Book ID:** {book['id']}")
        if book.get('category_name'):
            st.write(f"**Category:** {book['category_name']}")
        if book.get('publisher'):
            st.write(f"**Publisher:** {book['publisher']}")
        if book.get('description'):
            with st.expander("Description"):
                st.write(book['description'])
    
    with col_meta:
        st.write(f"**Chapters:** {len(book.get('chapters', []))}")
        st.write(f"**Added:** {format_date(book.get('created_at'))}")
    
    # Display chapters
    if book.get('chapters'):
        st.subheader("Chapters")
        for chapter in book['chapters']:
            display_chapter(book, chapter)
    
    st.divider()

######## browse_books - display_chapter ########
def display_chapter(book, chapter):
    """Display individual chapter with audio player"""
    chapter_col1, chapter_col2 = st.columns([3, 1])
    
    with chapter_col1:
        st.write(f"**Chapter {chapter['chapter_number']}:** {chapter['title']}")
        # Show duration if available
        if chapter.get('duration'):
            st.caption(f"Duration: {chapter['duration']}")
    
    with chapter_col2:
        audio_key = f"audio_{book['id']}_{chapter['chapter_number']}"
        
        if st.button("🎵 Play Audio", key=f"btn_{audio_key}", use_container_width=True):
            handle_audio_play(book, chapter, audio_key)


######## browse_books - handle_audio_play ########
def handle_audio_play(book, chapter, audio_key):
    """Handle audio playback for a chapter and record it"""
    user_id = st.session_state.get('user_id')
    
    if not user_id:
        st.error("Please login to play audio")
        return
    
    with st.spinner("Loading audio..."):
        audio_url = get_signed_audio_url(book['id'], chapter['title'])
    
    if audio_url:
        try:
            # ✅ Record this play in access_history
            record_audio_play(
                user_id=user_id,
                book_id=book['id'],
                chapter_id=chapter['id'],
                duration=0,  # You can track actual duration later
                progress=0   # You can track progress percentage later
            )
            
            # Display audio player
            audio_container = st.container()
            
            with audio_container:
                st.audio(audio_url, format="audio/mp3")
                
                # Download button
                try:
                    audio_response = requests.get(audio_url, timeout=30)
                    if audio_response.status_code == 200:
                        st.download_button(
                            label="📥 Download MP3",
                            data=audio_response.content,
                            file_name=f"{sanitize_filename(book['title'])}_Chapter_{chapter['chapter_number']}.mp3",
                            mime="audio/mp3",
                            key=f"dl_{audio_key}",
                            use_container_width=True
                        )
                    else:
                        st.warning("Download temporarily unavailable")
                except:
                    st.warning("Download temporarily unavailable")
                    
        except Exception as audio_error:
            st.error(f"Audio playback error: {audio_error}")
    else:
        st.error("Failed to load audio. Please try again.")


######## my_library - get_signed_audio_url ########
######## browse_books - get_signed_audio_url ########
def get_signed_audio_url(book_id, chapter_title):
    """Get signed URL from Flask API"""
    try:
        # Use the original audio-url endpoint, NOT the streaming one
        # encoded_title = urllib.parse.quote(chapter_title)
        # response = requests.get(
        #     f"{API_URL}/api/audio-url/{book_id}/{encoded_title}",
        #     timeout=10
        # )
        response = requests.get(
            f"{API_URL}/api/audio-url/{book_id}/{chapter_title}",  # No encoding
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            url = data.get('url')
            
            if url:
                print(f"Generated signed URL: {url}")
                return url
            else:
                print("No URL returned from API")
                return None
        else:
            print(f"Failed to get audio URL: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        st.error(f"Error getting audio URL: {str(e)}")
        print(f"Exception: {str(e)}")
        return None

######## my_library - record_audio_play ########
######## browse_books - record_audio_play ########
def record_audio_play(user_id, book_id, chapter_id=None, duration=0, progress=0):
    """Call Flask API to record audio play"""
    try:
        response = requests.post(
            f"{API_URL}/api/record-play",
            json={
                "user_id": user_id,
                "book_id": book_id,
                "chapter_id": chapter_id,
                "duration": duration,
                "progress": progress
            },
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error calling record API: {str(e)}")
        return False


######## my_library - sanitize_filename ########
######## browse_books - sanitize_filename ########
def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    import re
    return re.sub(r'[<>:"/\\|?*]', '', filename)


# Helper functions
######## browse_books - format_date ########
def format_date(date_string):
    """Format date string for display"""
    if not date_string:
        return "Unknown"
    try:
        from datetime import datetime
        date_obj = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        return date_obj.strftime('%b %d, %Y')
    except:
        return date_string
######## END - browse_books ########

def show_book_recommendations():
    """Show book recommendations"""
    # Your recommendation logic here
    pass