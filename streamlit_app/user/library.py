# streamlit_app/user/library.py
#########################
import streamlit as st
import streamlit.components.v1 as components
import requests
from datetime import datetime
# from components.helpers import format_date
from components.helpers import format_date, audio_player, get_signed_audio_url
from config import API_URL, DEBUG

def my_library():
    """Personal library with working audio tracking"""
    st.header("📖 My Personal Library")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🎵 Recently Played", "⭐ Favorites", "📥 Downloads", "📚 History"])
    
    with tab1:
        show_recently_played()
    with tab2:
        show_favorites()
    with tab3:
        show_downloads()
    with tab4:
        show_reading_history()


def show_recently_played():
    """Show recently played books"""
    st.subheader("Recently Played Books")
    
    try:
        user_id = st.session_state.get('user_id')
        if not user_id:
            st.info("Please login to view your listening history")
            return
        
        recent_books = get_recently_played(user_id, limit=8)
        
        if not recent_books:
            st.info("You haven't played any books yet. Start listening to see them here!")
            return
        
        for i, book in enumerate(recent_books):
            display_recent_book(book, i)
            
    except Exception as e:
        st.error("Error loading your history")
        if DEBUG:
            st.error(str(e))


def get_recently_played(user_id, limit=10):
    """Streamlit function to get recently played books from API"""
    try:
        response = requests.get(
            f"{API_URL}/api/get_recently-played",
            params={"user_id": user_id,
                    "limit": limit},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('data', [])
            else:
                st.error(f"API error: {data.get('error', 'Unknown error')}")
                return None
        else:
            st.error(f"Failed to fetch recently played: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return None



def display_recent_book(book, idx):
    with st.container():
        chapter_title = book.get("current_chapter")
        if not chapter_title:
            st.warning("No chapter file found for this book.")
            return
        
        st.write(f"**{book.get('title', 'Unknown Book')}**")
        st.write(f"**Chapter {book.get("chapter_number")}: {book.get("current_chapter")}**")
        st.caption(f"Last played: {format_date(book.get('last_played'))}")

        audio_url = get_signed_audio_url(book["id"], chapter_title)

        if audio_url:
            audio_player(
                user_id=st.session_state["user_id"],
                book_id=book["id"],
                chapter_id=book.get("chapter_id"),
                audio_url=audio_url
            )
        else:
            st.error("Could not generate signed audio URL.")

# def display_recent_book(book, index):
#     """
#     Display a single recently played book entry with progress + player.
#     Expected 'book' dict keys: id, title, author, cover_url, chapter_id, chapter_title,
#     accessed_at, duration, progress
#     """
#     with st.container():
        

#         cols = st.columns([1, 3])  # left: cover, right: details
        
#         # --- Left: Cover ---
#         with cols[0]:
#             cover_url = book.get("cover_url")
#             if cover_url:
#                 st.image(cover_url, use_column_width=True)
#             else:
#                 st.markdown("📘")  # fallback icon

#         # --- Right: Details ---
#         with cols[1]:
#             st.markdown(f"### {book.get('title','Untitled')}")
#             st.caption(f"by {book.get('author','Unknown Author')}")

#             accessed = format_date(book.get("accessed_at"))
#             st.markdown(f"*Last listened:* {accessed}")

#             # Progress info
#             duration = int(book.get("duration") or 0)
#             progress = int(book.get("progress") or 0)
#             if duration > 0:
#                 percent = int((progress / duration) * 100)
#                 st.progress(min(percent, 100))
#                 st.caption(f"{progress}s / {duration}s ({percent}%)")
#             else:
#                 st.caption("Not started")

#             # Audio playback
#             from components.helpers import get_signed_audio_url, audio_player
#             book_id = book.get("id")
#             chapter_id = book.get("chapter_id")
#             chapter_title = book.get("chapter_title", "unknown")

#             user_id = st.session_state.get("user_id")
#             audio_url = get_signed_audio_url(book["id"], chapter_title)
#             # audio_url = get_signed_audio_url(book_id, chapter_title)
#             if audio_url:
#         #         st.write(f"**{book.get('title', 'Unknown Book')}**")
#         # st.caption(f"Last played: {format_date(book.get('accessed_at'))}")

#         # # Use chapter_title from DB instead of "unknown"
#         # chapter_title = book.get("chapter_title") or "aud002.mp3"
#         # audio_url = get_signed_audio_url(book["id"], chapter_title)
        
#                 audio_player(user_id, book_id, chapter_id, audio_url)
#             else:
#                 st.warning("Audio not available")




# def update_playback_progress(user_id, book_id, chapter_id=None, duration=0, progress=0):
#     try:
#         # Convert to integers
#         progress_int = int(round(progress))
#         duration_int = int(round(duration))
        
#         print(f"📊 Sending to API: duration={duration_int}s, progress={progress_int}%")
#         print(f"📊 User: {user_id}, Book: {book_id}, Chapter: {chapter_id}")

#         payload = {
#             "user_id": user_id,
#             "book_id": book_id,
#             "chapter_id": chapter_id,
#             "duration": duration_int, 
#             "progress": progress_int
#         }
        
#         print(f"📤 Payload: {payload}")
        
#         response = requests.post(
#             f"{API_URL}/api/update-playback",
#             json=payload,
#             timeout=10
#         )
        
#         print(f"📥 Response status: {response.status_code}")
#         print(f"📥 Response text: {response.text}")
        
#         if response.status_code == 200:
#             data = response.json()
#             success = data.get('success', False)
#             print(f"✅ API response success: {success}")
#             return success
#         else:
#             print(f"❌ API call failed: {response.status_code}")
#             return False
            
#     except Exception as e:
#         print(f"❌ Error updating playback progress: {str(e)}")
#         return False



# Placeholder functions for other tabs
def show_favorites():
    st.info("Favorites functionality coming soon...")

def show_downloads():
    st.info("Downloads functionality coming soon...")

def show_reading_history():
    st.info("Reading history functionality coming soon...")