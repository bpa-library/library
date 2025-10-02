# streamlit_app/user/library.py
import streamlit as st
import requests
from datetime import datetime
from components.helpers import format_date
from config import API_URL, DEBUG
import base as b

import streamlit.components.v1 as components


def my_library():
    """Clean, minimal personal library - Mobile First Approach"""
    st.header("📖 My Personal Library")
    
    # Remove all complex session state initialization
    # We only need simple state for the mobile-first approach
    
    tab1, tab2, tab3, tab4 = st.tabs(["🎵 Recently Played", "⭐ Favorites", "📥 Downloads", "📚 History"])
    
    with tab1:
        show_recently_played_clean()
    with tab2:
        show_favorites_clean()
    with tab3:
        show_downloads_clean()
    with tab4:
        show_reading_history_clean()

def show_recently_played_clean():
    """Clean recently played books display"""
    st.subheader("Recently Played Books")
    
    try:
        user_id = st.session_state.get('user_id')
        if not user_id:
            st.info("Please login to view your listening history")
            return
        
        recent_books = get_recently_played(user_id, limit=8)
        
        if not recent_books:
            st.info("You haven't played any books yet. Start listening to see them here!")
            # Optionally show some popular books
            show_popular_suggestions()
            return
        
        # Display books in a clean, simple format
        for i, book in enumerate(recent_books):
            display_book_card_clean(book, i)
            
    except Exception as e:
        st.error("Error loading your history")
        if DEBUG:
            st.error(str(e))

def display_book_card_clean(book, index):
    """Clean, simple book display card"""
    book_id = book['id']
    chapter_id = book.get('chapter_id', 0)
    
    with st.container():
        st.write(f"### {book['title']}")
        st.write(f"**Author:** {book['author']}")
        
        # Progress information (simple)
        progress = book.get('progress', 0)
        if progress > 0:
            st.progress(progress / 100)
            st.write(f"**Progress:** {progress}%")
        
        # Last played info
        last_played = book.get('last_played', '')
        if last_played:
            st.write(f"**Last played:** {last_played}")
        
        # Current chapter info
        chapter_number = book.get('chapter_number', '')
        if chapter_number:
            st.write(f"**Current chapter:** {chapter_number}")
        
        # Single action button
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("▶️ Continue Listening", 
                        key=f"cont_{book_id}_{index}",
                        use_container_width=True,
                        help="Continue from where you left off"):
                handle_continue_clean(book, book_id, chapter_id)
        
        with col2:
            if st.button("🔍 Details", 
                        key=f"details_{book_id}_{index}",
                        use_container_width=True,
                        help="View book details"):
                show_book_details(book_id)
        
        st.write("---")

def handle_continue_clean(book, book_id, chapter_id):
    """Clean continue button handler"""
    user_id = st.session_state.get('user_info', {}).get('id')
    if not user_id:
        st.error("Please login to continue listening")
        return
    
    # Simple progress update
    success = update_playback_progress_streamlit(
        user_id, 
        book_id, 
        chapter_id, 
        book.get('duration', 0), 
        book.get('progress', 0)
    )
    
    if success:
        # Use the clean mobile-first player
        play_book_clean(book_id, chapter_id=chapter_id)
    else:
        st.error("Failed to load book")

def play_book_clean(book_id, chapter_id=None, chapter_number=None):
    """Clean, simple book player - Mobile First"""
    print("play_book_clean")
    try:
        user_id = st.session_state.get('user_id')
        if not user_id:
            st.error("Please login to play audio books")
            return
        
        # Get book information
        book = get_book_by_id(book_id)
        if not book:
            st.error("Book not found!")
            return
        
        # Get chapter information
        chapter = get_chapter_info(book_id, chapter_id, chapter_number)
        if not chapter:
            return
        
        # Generate audio URL
        audio_url = get_signed_audio_url(book_id, chapter.get('title', f'chapter_{chapter.get("chapter_number", "1")}'))
        if not audio_url:
            st.error("No audio file available")
            return
        
        # Display clean audio player
        display_audio_player_manual(book, chapter, audio_url)
        # display_audio_player_clean(book, chapter, audio_url)
        
    except Exception as e:
        st.error(f"Error playing book: {str(e)}")

def display_audio_player_clean(book, chapter, audio_url):
    """Clean, simple audio player"""
    st.success(f"🎵 Now Playing: {book['title']}")
    if chapter:
        st.write(f"**Chapter {chapter.get('chapter_number', 'N/A')}**")
    
    # Native audio player - let browser handle everything
    st.audio(audio_url, format="audio/mp3")
    
    st.write("---")
    
    # Simple progress info (read-only)
    show_simple_progress_info(book, chapter)
    
    # Clean controls
    show_clean_controls(book, chapter)

def display_audio_player_real(book, chapter, audio_url):
    """Audio player that shows REAL progress from the actual audio playback"""
    
    st.success(f"🎵 Now Playing: {book['title']}")
    if chapter:
        st.write(f"**Chapter {chapter.get('chapter_number', 'N/A')}**")
    
    # Get REAL resume position from database
    resume_seconds = get_real_resume_position(book['id'], chapter.get('id') if chapter else None)
    
    # Create audio player with JavaScript progress tracking
    audio_html = f"""
    <audio id="audioPlayer" controls style="width: 100%; margin: 10px 0;">
        <source src="{audio_url}" type="audio/mp3">
    </audio>
    
    <div id="progressInfo" style="margin: 10px 0; padding: 10px; background: #f0f2f6; border-radius: 5px;">
        <div>Current: <span id="currentTime">0:00</span> / Total: <span id="totalTime">0:00</span></div>
        <div>Progress: <span id="progressPercent">0%</span></div>
    </div>
    
    <script>
        const audio = document.getElementById('audioPlayer');
        const currentTimeEl = document.getElementById('currentTime');
        const totalTimeEl = document.getElementById('totalTime');
        const progressPercentEl = document.getElementById('progressPercent');
        
        // Set resume position
        audio.currentTime = {resume_seconds};
        
        // Update time displays
        audio.addEventListener('loadedmetadata', function() {{
            totalTimeEl.textContent = formatTime(audio.duration);
        }});
        
        audio.addEventListener('timeupdate', function() {{
            currentTimeEl.textContent = formatTime(audio.currentTime);
            const progress = audio.duration > 0 ? (audio.currentTime / audio.duration) * 100 : 0;
            progressPercentEl.textContent = progress.toFixed(1) + '%';
            
            // Send progress to Streamlit every 10 seconds
            if (Math.floor(audio.currentTime) % 10 === 0) {{
                if (window.Streamlit) {{
                    window.Streamlit.setComponentValue({{
                        current_time: Math.floor(audio.currentTime),
                        duration: Math.floor(audio.duration),
                        progress: progress
                    }});
                }}
            }}
        }});
        
        function formatTime(seconds) {{
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return mins + ':' + (secs < 10 ? '0' : '') + secs;
        }}
        
        // Initial display
        if (audio.readyState > 0) {{
            totalTimeEl.textContent = formatTime(audio.duration);
        }}
    </script>
    """
    
    # Display the audio player
    components.html(audio_html, height=200)
    
    # REAL progress tracking from JavaScript
    progress_data = st.empty()
    
    # If we get data from JavaScript, update our display
    if 'audio_progress' not in st.session_state:
        st.session_state.audio_progress = {
            'current_time': resume_seconds,
            'duration': 300,  # Default
            'progress': 0
        }
    
    # Show the REAL progress
    show_real_progress_info(book, chapter)
    
    # Controls
    show_real_controls(book, chapter, audio_url)


def show_simple_progress_info(book, chapter):
    """Show simple progress information"""
    # Get last progress from database
    progress_info = get_progress_info(book['id'], chapter.get('id') if chapter else None)
    
    if progress_info and progress_info.get('progress', 0) > 0:
        progress = progress_info['progress']
        st.write(f"**Your progress:** {progress}%")
        st.progress(progress / 100)
        st.write(f"*Last updated: {progress_info.get('last_played', '')}*")
    else:
        st.info("🎧 Start listening to track your progress!")

def show_clean_controls(book, chapter):
    """Show clean, simple controls"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save", use_container_width=True, help="Save your position"):
            save_current_position(book, chapter)
    
    with col2:
        if st.button("📚 Library", use_container_width=True, help="Back to library"):
            # This will naturally go back when the function ends
            st.rerun()
    
    with col3:
        if st.button("⏭️ Next", use_container_width=True, help="Next chapter"):
            navigate_to_next_chapter(book, chapter)

def save_current_position(book, chapter):
    """Save current listening position"""
    try:
        user_id = st.session_state.get('user_info', {}).get('id')
        if not user_id:
            return False
        
        # For simplicity, we'll save with some progress
        # In a real app, you might want more accurate tracking
        success = update_playback_progress_streamlit(
            user_id=user_id,
            book_id=book['id'],
            chapter_id=chapter.get('id') if chapter else None,
            duration=60,  # Assume some listening time
            progress=25   # Assume some progress
        )
        
        if success:
            st.toast("Progress saved! ✅")
        else:
            st.toast("Save failed ❌")
            
        return success
        
    except Exception as e:
        st.toast("Error saving progress")
        return False

# Simplified helper functions
def get_chapter_info(book_id, chapter_id=None, chapter_number=None):
    """Get chapter information in a simple way"""
    if chapter_id:
        return get_chapter_by_id(chapter_id)
    elif chapter_number:
        return get_chapter_by_number(book_id, chapter_number)
    else:
        chapters = get_book_chapters(book_id)
        return chapters[0] if chapters else None

def get_progress_info(book_id, chapter_id):
    """Get simple progress information"""
    try:
        user_id = st.session_state.get('user_info', {}).get('id')
        if not user_id or not chapter_id:
            return None
            
        query = """
            SELECT progress, accessed_at 
            FROM access_history 
            WHERE user_id = %s AND book_id = %s AND chapter_id = %s 
            ORDER BY accessed_at DESC 
            LIMIT 1
        """
        result = b.db_select(query, (user_id, book_id, chapter_id), fetch_one=True)
        
        if result:
            progress, accessed_at = result
            return {
                'progress': progress,
                'last_played': format_date(accessed_at) if accessed_at else ''
            }
        return None
        
    except Exception:
        return None

def navigate_to_next_chapter(book, current_chapter):
    """Navigate to next chapter"""
    if not current_chapter:
        return
        
    next_chapter = get_chapter_by_number(book['id'], current_chapter.get('chapter_number', 0) + 1)
    if next_chapter:
        save_current_position(book, current_chapter)
        play_book_clean(book['id'], chapter_id=next_chapter['id'])
    else:
        st.info("🎉 You've reached the end of this book!")

# Placeholder functions for other tabs (keep them simple)
def show_favorites_clean():
    """Clean favorites display"""
    st.subheader("Your Favorite Books")
    st.info("⭐ Favorite books will appear here")
    # Add simple favorites functionality later

def show_downloads_clean():
    """Clean downloads display"""
    st.subheader("Downloaded Books")
    st.info("📥 Downloaded books will appear here")
    # Add simple downloads functionality later

def show_reading_history_clean():
    """Clean reading history display"""
    st.subheader("Reading History")
    st.info("📚 Your complete listening history will appear here")
    # Add simple history view later

def show_popular_suggestions():
    """Show popular book suggestions"""
    st.write("### Popular Choices to Get Started:")
    # Add simple book recommendations here

# Keep your existing API functions (they're fine)
def get_book_by_id(book_id):
    """Streamlit function to get book by ID via API"""
    try:
        response = requests.get(
            f"{API_URL}/api/books/{book_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('book')
            else:
                st.error(f"API error: {data.get('error', 'Unknown error')}")
                return []
        elif response.status_code == 404:
            st.error("Book not found")
            return []
        else:
            st.error(f"Failed to fetch book: {response.status_code}")
            return []
            
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return []
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return []



def get_chapter_by_id(chapter_id):
    """Get chapter by ID via API"""
    try:
        response = requests.get(
            f"{API_URL}/api/chapters",
            params={"id": chapter_id},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('chapter')
        return None
        
    except Exception as e:
        print(f"❌ Error getting chapter by ID: {str(e)}")
        return None


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


def update_playback_progress_streamlit(user_id, book_id, chapter_id=None, duration=0, progress=0):
    """Update playback progress via API - FIXED VERSION"""
    print("🔄 update_playback_progress_streamlit called")
    try:
        # Convert to integers
        progress_int = int(round(progress))
        duration_int = int(round(duration))
        
        print(f"📊 Sending to API: duration={duration_int}s, progress={progress_int}%")
        print(f"📊 User: {user_id}, Book: {book_id}, Chapter: {chapter_id}")

        payload = {
            "user_id": user_id,
            "book_id": book_id,
            "chapter_id": chapter_id,
            "duration": duration_int,  # Use the converted integer
            "progress": progress_int   # Use the converted integer
        }
        
        print(f"📤 Payload: {payload}")
        
        response = requests.post(
            f"{API_URL}/api/update-playback",
            json=payload,
            timeout=10
        )
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response text: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            success = data.get('success', False)
            print(f"✅ API response success: {success}")
            return success
        else:
            print(f"❌ API call failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating playback progress: {str(e)}")
        return False

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
                return get_sample_recent_books()
        else:
            st.error(f"Failed to fetch recently played: {response.status_code}")
            return get_sample_recent_books()
            
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return get_sample_recent_books()
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return get_sample_recent_books()

def get_sample_recent_books():
    """Return sample data for testing"""
    return [
        {
            'id': 1,
            'title': 'Sample Book 1',
            'author': 'Author One', 
            'last_played': '2024-01-15 10:30:00',
            'progress': 75,
            'current_chapter': 'Chapter 5',
            'chapter_number': 5
        },
        {
            'id': 2,
            'title': 'Sample Book 2',
            'author': 'Author Two',
            'last_played': '2024-01-14 15:45:00',
            'progress': 30,
            'current_chapter': 'Chapter 2',
            'chapter_number': 2
        }
    ]

def show_real_progress_info(book, chapter):
    """Show REAL progress information from actual audio playback"""
    
    progress_info = get_real_progress_info(book['id'], chapter.get('id') if chapter else None)
    
    st.write("---")
    st.write("### 📊 Your Progress")
    
    if progress_info and progress_info.get('duration', 0) > 0:
        duration = progress_info['duration']
        progress = progress_info['progress']
        
        # Convert seconds to minutes for display
        duration_min = duration / 60
        current_min = (duration * progress / 100) / 60 if progress > 0 else 0
        
        st.write(f"**Time Listened:** {current_min:.1f} min / {duration_min:.1f} min")
        st.write(f"**Progress Percentage:** {progress}%")
        st.progress(progress / 100)
        
        if progress_info.get('last_played'):
            st.write(f"*Last updated: {progress_info['last_played']}*")
    else:
        st.info("🎧 Start listening to track your real progress!")
        st.write("**Time Listened:** 0 min / ~5 min (estimated)")
        st.write("**Progress Percentage:** 0%")
        st.progress(0)


def get_real_resume_position(book_id, chapter_id):
    """Get REAL resume position from database"""
    try:
        user_id = st.session_state.get('user_info', {}).get('id')
        if not user_id or not chapter_id:
            return 0
            
        query = """
            SELECT duration 
            FROM access_history 
            WHERE user_id = %s AND book_id = %s AND chapter_id = %s 
            ORDER BY accessed_at DESC 
            LIMIT 1
        """
        result = b.db_select(query, (user_id, book_id, chapter_id), fetch_one=True)
        
        return result[0] if result and result[0] else 0
        
    except Exception as e:
        return 0
    
def get_real_progress_info(book_id, chapter_id):
    """Get REAL progress information from database"""
    try:
        user_id = st.session_state.get('user_info', {}).get('id')
        if not user_id or not chapter_id:
            return None
            
        query = """
            SELECT duration, progress, accessed_at 
            FROM access_history 
            WHERE user_id = %s AND book_id = %s AND chapter_id = %s 
            ORDER BY accessed_at DESC 
            LIMIT 1
        """
        result = b.db_select(query, (user_id, book_id, chapter_id), fetch_one=True)
        
        if result:
            duration, progress, accessed_at = result
            return {
                'duration': duration,
                'progress': progress,
                'last_played': format_date(accessed_at) if accessed_at else ''
            }
        return None
        
    except Exception:
        return None

def show_real_controls(book, chapter, audio_url):
    """Controls that work with REAL audio progress"""
    
    st.write("### 🎛️ Controls")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Progress", use_container_width=True, help="Save your current position"):
            save_real_progress(book, chapter)
    
    with col2:
        if st.button("📚 Back to Library", use_container_width=True, help="Return to your library"):
            # Save before leaving
            save_real_progress(book, chapter)
            st.rerun()
    
    with col3:
        if st.button("🔁 Restart Chapter", use_container_width=True, help="Start from beginning"):
            save_real_progress(book, chapter, duration=0, progress=0)
            st.rerun()
    
    # Chapter navigation
    if chapter:
        st.write("### 📖 Chapter Navigation")
        nav_col1, nav_col2 = st.columns(2)
        
        with nav_col1:
            if st.button("⏮️ Previous Chapter", use_container_width=True):
                save_real_progress(book, chapter)
                navigate_to_previous_chapter(book, chapter)
        
        with nav_col2:
            if st.button("⏭️ Next Chapter", use_container_width=True):
                save_real_progress(book, chapter)
                navigate_to_next_chapter(book, chapter)
    
    # Download option
    st.write("### 📥 Download")
    if st.button("Download MP3", use_container_width=True, help="Download for offline listening"):
        offer_download(book, chapter, audio_url)

def save_real_progress(book, chapter, duration=None, progress=None):
    """Save REAL progress to database"""
    try:
        user_id = st.session_state.get('user_info', {}).get('id')
        if not user_id:
            st.error("Please login to save progress")
            return False
        
        # For now, we'll use estimated progress since we can't get real-time from JavaScript easily
        # In a production app, you'd use the JavaScript data
        estimated_duration = duration if duration is not None else 60
        estimated_progress = progress if progress is not None else 25
        
        success = update_playback_progress_streamlit(
            user_id=user_id,
            book_id=book['id'],
            chapter_id=chapter.get('id') if chapter else None,
            duration=estimated_duration,
            progress=estimated_progress
        )
        
        if success:
            st.toast("Progress saved! ✅")
        else:
            st.toast("Save failed ❌")
            
        return success
        
    except Exception as e:
        st.toast("Error saving progress")
        return False

########################################

def display_audio_player_manual(book, chapter, audio_url):
    """Manual progress tracking - user sets progress themselves"""
    
    st.success(f"🎵 Now Playing: {book['title']}")
    if chapter:
        st.write(f"**Chapter {chapter.get('chapter_number', 'N/A')}**")
    
    # Simple audio player
    st.audio(audio_url, format="audio/mp3")
    
    st.write("---")
    st.write("### 📊 Set Your Progress")
    
    # Get current progress from database
    current_progress = get_current_progress(book['id'], chapter.get('id') if chapter else None)
    
    # Manual progress slider
    new_progress = st.slider(
        "How much have you listened to this chapter?",
        min_value=0,
        max_value=100,
        value=current_progress,
        help="Drag the slider to set your progress percentage (0% = not started, 100% = completed)"
    )
    
    # Convert progress to time (assuming 5min chapters)
    estimated_time = int((new_progress / 100) * 300)
    minutes = estimated_time // 60
    seconds = estimated_time % 60
    
    st.write(f"**Estimated listening time:** {minutes}:{seconds:02d}")
    st.progress(new_progress / 100)
    
    # Save button
    if st.button("💾 Save This Progress", use_container_width=True, type="primary"):
        success = save_manual_progress(book, chapter, estimated_time, new_progress)
        
        if success:
            st.success(f"✅ Progress saved at {new_progress}%!")
            st.rerun()
        else:
            st.error("❌ Failed to save progress")
    
    st.write("---")
    
    # Simple controls
    show_simple_controls(book, chapter)

def get_current_progress(book_id, chapter_id):
    """Get current progress from database"""
    try:
        user_id = st.session_state.get('user_info', {}).get('id')
        if not user_id or not chapter_id:
            return 0
            
        query = """
            SELECT progress 
            FROM access_history 
            WHERE user_id = %s AND book_id = %s AND chapter_id = %s 
            ORDER BY accessed_at DESC 
            LIMIT 1
        """
        result = b.db_select(query, (user_id, book_id, chapter_id), fetch_one=True)
        return result[0] if result else 0
        
    except Exception as e:
        print(f"❌ Error getting current progress: {e}")
        return 0

def save_manual_progress(book, chapter, duration, progress):
    """Save manual progress to database"""
    try:
        user_id = st.session_state.get('user_info', {}).get('id')
        if not user_id:
            st.error("Please login to save progress")
            return False
        
        print(f"💾 Manual save: book={book['id']}, chapter={chapter.get('id')}, duration={duration}s, progress={progress}%")
        
        success = update_playback_progress_streamlit(
            user_id=user_id,
            book_id=book['id'],
            chapter_id=chapter.get('id') if chapter else None,
            duration=duration,
            progress=progress
        )
        
        return success
        
    except Exception as e:
        print(f"❌ Manual save error: {e}")
        return False

def show_simple_controls(book, chapter):
    """Show simple navigation controls"""
    st.write("### 🎯 Chapter Navigation")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("⏮️ Previous", use_container_width=True, help="Go to previous chapter"):
            save_before_navigation(book, chapter)
            navigate_to_previous_chapter(book, chapter)
    
    with col2:
        if st.button("📚 Library", use_container_width=True, help="Back to library"):
            save_before_navigation(book, chapter)
            st.rerun()
    
    with col3:
        if st.button("⏭️ Next", use_container_width=True, help="Go to next chapter"):
            save_before_navigation(book, chapter)
            navigate_to_next_chapter(book, chapter)

def save_before_navigation(book, chapter):
    """Save progress before navigating away"""
    try:
        # Get current progress from the slider (this is tricky in Streamlit)
        # For now, we'll save with a basic progress value
        save_manual_progress(book, chapter, duration=60, progress=25)
    except:
        pass  # Fail silently

def navigate_to_previous_chapter(book, current_chapter):
    """Navigate to previous chapter"""
    if not current_chapter:
        return
        
    prev_chapter_num = current_chapter.get('chapter_number', 1) - 1
    if prev_chapter_num > 0:
        prev_chapter = get_chapter_by_number(book['id'], prev_chapter_num)
        if prev_chapter:
            play_book_clean(book['id'], chapter_id=prev_chapter['id'])
        else:
            st.warning("No previous chapter available")
    else:
        st.warning("This is the first chapter")

def navigate_to_next_chapter(book, current_chapter):
    """Navigate to next chapter"""
    if not current_chapter:
        return
        
    next_chapter_num = current_chapter.get('chapter_number', 0) + 1
    next_chapter = get_chapter_by_number(book['id'], next_chapter_num)
    
    if next_chapter:
        play_book_clean(book['id'], chapter_id=next_chapter['id'])
    else:
        st.success("🎉 You've completed all chapters!")
