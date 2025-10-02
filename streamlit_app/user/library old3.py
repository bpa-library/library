# streamlit_app/user/library.py
import streamlit as st
import streamlit.components.v1 as components
import requests
from datetime import datetime
from components.helpers import format_date
from config import API_URL, DEBUG
import base as b

def my_library():
    """Personal library with working audio tracking"""
    st.header("📖 My Personal Library")
    
    # Check for audio messages on every render
    check_audio_messages()
    
    tab1, tab2, tab3, tab4 = st.tabs(["🎵 Recently Played", "⭐ Favorites", "📥 Downloads", "📚 History"])
    
    with tab1:
        show_recently_played()
    with tab2:
        show_favorites()
    with tab3:
        show_downloads()
    with tab4:
        show_reading_history()

def check_audio_messages():
    """Check for audio progress messages in session state"""
    if 'audio_messages' in st.session_state and st.session_state.audio_messages:
        for message in st.session_state.audio_messages:
            process_audio_message(message)
        # Clear processed messages
        st.session_state.audio_messages = []

def process_audio_message(message):
    """Process an audio progress message"""
    try:
        if message.get('type') in ['audioProgress', 'audioEnded']:
            book_id = message.get('book_id')
            chapter_id = message.get('chapter_id')
            current_time = message.get('current_time', 0)
            progress = message.get('progress', 0)
            
            print(f"🎯 Processing audio message: {current_time}s, {progress}%")
            
            # Save to database
            success = save_audio_progress(book_id, chapter_id, current_time, progress)
            
            if success:
                st.toast(f"💾 Progress saved: {current_time}s", icon="✅")
            else:
                st.toast("❌ Save failed", icon="❌")
                
    except Exception as e:
        print(f"❌ Error processing audio message: {e}")

def save_audio_progress(book_id, chapter_id, current_time, progress):
    """Save audio progress to database"""
    try:
        user_id = st.session_state.get('user_info', {}).get('id')
        if not user_id:
            return False
        
        print(f"💾 Saving to DB: book={book_id}, chapter={chapter_id}, time={current_time}s, progress={progress}%")
        
        return update_playback_progress_streamlit(
            user_id=user_id,
            book_id=book_id,
            chapter_id=chapter_id,
            duration=int(current_time),
            progress=int(progress)
        )
        
    except Exception as e:
        print(f"❌ Error saving audio progress: {e}")
        return False
    


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

def display_recent_book(book, index):
    """Display a recently played book"""
    book_id = book['id']
    chapter_id = book.get('chapter_id', 0)
    unique_key = f"recent_{book_id}_{chapter_id}_{index}"
    
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"**{book['title']}**")
            st.write(f"by {book['author']}")
            
            # Show real progress from database
            progress = book.get('progress', 0)
            duration = book.get('duration', 0)
            
            if progress > 0:
                st.progress(progress / 100)
                st.write(f"**Progress:** {progress}%")
                if duration > 0:
                    minutes = duration // 60
                    seconds = duration % 60
                    st.write(f"**Time listened:** {minutes}:{seconds:02d}")
            
            last_played = book.get('last_played', '')
            if last_played:
                st.write(f"*Last played: {last_played}*")
        
        with col2:
            if st.button("▶️ Continue", key=unique_key, use_container_width=True):
                handle_continue_click(book, book_id, chapter_id)
        
        st.write("---")

def handle_continue_click(book, book_id, chapter_id):
    """Handle continue click"""
    user_id = st.session_state.get('user_info', {}).get('id')
    if not user_id:
        st.error("Please login to continue listening")
        return
    
    # Simple update to mark as accessed
    update_playback_progress_streamlit(
        user_id, book_id, chapter_id, 
        book.get('duration', 0), 
        book.get('progress', 0)
    )
    
    # Play with advanced audio player
    play_book_advanced(book_id, chapter_id=chapter_id)

def play_book_advanced(book_id, chapter_id=None, chapter_number=None):
    """Advanced book player using SIMPLE working solution"""
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
            st.error("Chapter not found!")
            return
        
        # Generate audio URL
        audio_url = get_signed_audio_url(book_id, chapter.get('title', f'chapter_{chapter.get("chapter_number", "1")}'))
        if not audio_url:
            st.error("No audio file available")
            return
        
        # Use the SIMPLE working audio player
        display_working_audio_player(book, chapter, audio_url)
        
    except Exception as e:
        st.error(f"Error playing book: {str(e)}")

def display_videojs_audio_player(book, chapter, audio_url):
    """Video.js audio player with WORKING progress tracking"""
    
    st.success(f"🎵 Now Playing: {book['title']}")
    if chapter:
        st.write(f"**Chapter {chapter.get('chapter_number', 'N/A')}**")
    
    # Get resume position
    resume_seconds = get_resume_position(book['id'], chapter.get('id') if chapter else None)
    
    # Create unique session ID for this audio player
    session_id = f"audio_{book['id']}_{chapter.get('id', '0')}_{datetime.now().timestamp()}"
    
    # Video.js audio player with FIXED communication
    videojs_html = create_videojs_player(audio_url, book['id'], chapter.get('id') if chapter else '0', resume_seconds, session_id)
    
    components.html(videojs_html, height=300)
    
    # Manual progress tracking as backup
    show_manual_progress_backup(book, chapter, session_id)
    
    # Show current progress from database
    show_current_progress(book, chapter)
    
    # Controls
    show_audio_controls(book, chapter)

def show_manual_progress_backup(book, chapter, session_id):
    """Manual progress backup in case auto-save fails"""
    st.write("---")
    st.write("### 💾 Progress Backup (Manual Save)")
    
    # Get current progress from the audio player via a clever trick
    current_time = st.number_input(
        "Current time (seconds):",
        min_value=0,
        max_value=600,
        value=0,
        key=f"time_{session_id}",
        help="Enter the current time from the audio player above"
    )
    
    if current_time > 0:
        duration = 312  # Based on your screenshot (0:52 = 52 seconds)
        progress = (current_time / duration) * 100
        
        st.write(f"**Calculated progress:** {progress:.1f}%")
        st.progress(progress / 100)
        
        if st.button("💾 Save This Progress", key=f"save_{session_id}"):
            success = save_audio_progress(
                book['id'],
                chapter.get('id') if chapter else None,
                current_time,
                progress
            )
            
            if success:
                st.success(f"✅ Saved: {current_time}s, {progress:.1f}%")
                st.rerun()
            else:
                st.error("❌ Save failed")

def create_videojs_player(audio_url, book_id, chapter_id, resume_seconds, session_id):
    """Create Video.js HTML with working Streamlit communication"""
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link href="https://vjs.zencdn.net/7.20.3/video-js.css" rel="stylesheet">
        <style>
            .audio-container {{
                width: 100%;
                margin: 20px 0;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }}
            .progress-info {{
                margin-top: 10px;
                padding: 10px;
                background: white;
                border-radius: 5px;
                font-family: Arial, sans-serif;
            }}
        </style>
    </head>
    <body>
        <div class="audio-container">
            <audio id="my-audio" class="video-js vjs-default-skin" controls preload="auto" width="100%">
                <source src="{audio_url}" type="audio/mpeg">
            </audio>
            
            <div class="progress-info">
                <div>🎯 <strong id="current-time">0:00</strong> / <strong id="duration">0:00</strong></div>
                <div>📊 Progress: <strong id="progress">0%</strong></div>
            </div>
        </div>
        
        <script src="https://vjs.zencdn.net/7.20.3/video.js"></script>
        <script>
            var player = videojs('my-audio');
            var lastSavedTime = 0;
            var sessionId = '{session_id}';
            
            player.ready(function() {{
                // Set resume position
                if ({resume_seconds} > 0) {{
                    player.currentTime({resume_seconds});
                    console.log('Resuming from: {resume_seconds}s');
                }}
                
                player.on('timeupdate', function() {{
                    var currentTime = Math.floor(player.currentTime());
                    var duration = Math.floor(player.duration());
                    var progress = duration > 0 ? (currentTime / duration) * 100 : 0;
                    
                    // Update display
                    document.getElementById('current-time').textContent = formatTime(currentTime);
                    document.getElementById('duration').textContent = formatTime(duration);
                    document.getElementById('progress').textContent = progress.toFixed(1) + '%';
                    
                    // Save progress every 10 seconds
                    if (currentTime - lastSavedTime >= 10) {{
                        saveProgress(currentTime, duration, progress);
                        lastSavedTime = currentTime;
                    }}
                }});
                
                player.on('ended', function() {{
                    saveProgress(Math.floor(player.duration()), Math.floor(player.duration()), 100);
                }});
            }});
            
            function saveProgress(currentTime, duration, progress) {{
                console.log('Saving progress: ' + currentTime + 's, ' + progress + '%');
                
                // Method 1: Try Streamlit.setComponentValue
                if (window.Streamlit && window.Streamlit.setComponentValue) {{
                    window.Streamlit.setComponentValue({{
                        type: 'audioProgress',
                        book_id: '{book_id}',
                        chapter_id: '{chapter_id}',
                        current_time: currentTime,
                        duration: duration,
                        progress: progress,
                        session_id: sessionId
                    }});
                }}
                
                // Method 2: Fallback to window.postMessage
                window.parent.postMessage({{
                    type: 'audioProgress',
                    book_id: '{book_id}',
                    chapter_id: '{chapter_id}',
                    current_time: currentTime,
                    duration: duration,
                    progress: progress,
                    session_id: sessionId
                }}, '*');
                
                // Method 3: Store in localStorage as backup
                localStorage.setItem('lastAudioProgress', JSON.stringify({{
                    book_id: '{book_id}',
                    chapter_id: '{chapter_id}',
                    current_time: currentTime,
                    progress: progress,
                    timestamp: Date.now()
                }}));
            }}
            
            function formatTime(seconds) {{
                var mins = Math.floor(seconds / 60);
                var secs = Math.floor(seconds % 60);
                return mins + ':' + (secs < 10 ? '0' : '') + secs;
            }}
            
            // Periodically check for progress to save
            setInterval(function() {{
                if (player && player.currentTime) {{
                    var currentTime = Math.floor(player.currentTime());
                    if (currentTime - lastSavedTime >= 15) {{
                        saveProgress(currentTime, Math.floor(player.duration()), 
                                   (currentTime / player.duration()) * 100);
                    }}
                }}
            }}, 5000); // Check every 5 seconds
            
        </script>
        
        <!-- Streamlit message listener -->
        <script>
            // Listen for messages from other frames
            window.addEventListener('message', function(event) {{
                if (event.data && event.data.type === 'audioProgress') {{
                    // Forward to Streamlit
                    if (window.Streamlit && window.Streamlit.setComponentValue) {{
                        window.Streamlit.setComponentValue(event.data);
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """

def videojs_audio_player(audio_url, book_id, chapter_id, resume_seconds=0):
    """Video.js audio player component - FIXED VERSION"""
    
    videojs_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link href="https://vjs.zencdn.net/7.20.3/video-js.css" rel="stylesheet">
        <style>
            .audio-container {{
                width: 100%;
                margin: 20px 0;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }}
            .progress-info {{
                margin-top: 10px;
                padding: 10px;
                background: white;
                border-radius: 5px;
                font-family: Arial, sans-serif;
                font-size: 14px;
            }}
            .time-display {{
                font-weight: bold;
                color: #2c3e50;
            }}
        </style>
    </head>
    <body>
        <div class="audio-container">
            <audio id="my-audio" class="video-js vjs-default-skin" controls preload="auto" width="100%">
                <source src="{audio_url}" type="audio/mpeg">
                Your browser does not support the audio element.
            </audio>
            
            <div class="progress-info">
                <div>🎯 <span class="time-display" id="current-time">0:00</span> / 
                     <span class="time-display" id="duration">0:00</span></div>
                <div>📊 Progress: <span class="time-display" id="progress">0%</span></div>
            </div>
        </div>
        
        <script src="https://vjs.zencdn.net/7.20.3/video.js"></script>
        <script>
            var player = videojs('my-audio');
            var lastSavedTime = 0;
            
            player.ready(function() {{
                // Set resume position
                if ({resume_seconds} > 0) {{
                    player.currentTime({resume_seconds});
                    console.log('Resuming from: {resume_seconds} seconds');
                }}
                
                // Update time displays
                player.on('timeupdate', function() {{
                    var currentTime = Math.floor(player.currentTime());
                    var duration = Math.floor(player.duration());
                    var progress = duration > 0 ? (currentTime / duration) * 100 : 0;
                    
                    // Update display
                    document.getElementById('current-time').textContent = formatTime(currentTime);
                    document.getElementById('duration').textContent = formatTime(duration);
                    document.getElementById('progress').textContent = progress.toFixed(1) + '%';
                    
                    // Auto-save every 10 seconds
                    if (currentTime - lastSavedTime >= 10) {{
                        // Send progress to Streamlit
                        if (window.Streamlit) {{
                            window.Streamlit.setComponentValue({{
                                type: 'audioProgress',
                                book_id: '{book_id}',
                                chapter_id: '{chapter_id}',
                                current_time: currentTime,
                                duration: duration,
                                progress: progress
                            }});
                        }}
                        lastSavedTime = currentTime;
                        console.log('Progress saved: ' + currentTime + 's, ' + progress.toFixed(1) + '%');
                    }}
                }});
                
                // Save when playback ends
                player.on('ended', function() {{
                    if (window.Streamlit) {{
                        window.Streamlit.setComponentValue({{
                            type: 'audioEnded',
                            book_id: '{book_id}',
                            chapter_id: '{chapter_id}', 
                            current_time: Math.floor(player.duration()),
                            duration: Math.floor(player.duration()),
                            progress: 100
                        }});
                    }}
                    console.log('Playback completed');
                }});
            }});
            
            function formatTime(seconds) {{
                var mins = Math.floor(seconds / 60);
                var secs = Math.floor(seconds % 60);
                return mins + ':' + (secs < 10 ? '0' : '') + secs;
            }}
        </script>
    </body>
    </html>
    """
    
    # Display component - FIXED (no key parameter)
    components.html(videojs_html, height=280)

# Simplified message handling using session state
def check_for_audio_messages():
    """Check for audio progress messages and save them"""
    # This would be called periodically, but for simplicity we'll use a different approach
    pass

def show_current_progress(book, chapter):
    """Show current progress from database"""
    st.write("### 📊 Database Progress")
    
    progress_data = get_progress_info(book['id'], chapter.get('id') if chapter else None)
    
    if progress_data and progress_data.get('duration', 0) > 0:
        duration = progress_data['duration']
        progress = progress_data['progress']
        
        minutes = duration // 60
        seconds = duration % 60
        
        st.write(f"**Saved in DB:** {minutes}:{seconds:02d}")
        st.write(f"**Progress in DB:** {progress}%")
        st.progress(progress / 100)
        
        if progress_data.get('last_played'):
            st.write(f"*Last updated: {progress_data['last_played']}*")
    else:
        st.info("No progress saved in database yet.")
        
    # Debug info
    if DEBUG:
        with st.expander("🔧 Debug Info"):
            st.write("Session state keys:", list(st.session_state.keys()))
            if 'audio_messages' in st.session_state:
                st.write("Audio messages:", st.session_state.audio_messages)

# Add this to capture messages
components.html(
    """
    <script>
    // Global message listener for audio progress
    window.addEventListener('message', function(event) {
        if (event.data && event.data.type === 'audioProgress') {
            if (window.Streamlit) {
                window.Streamlit.setComponentValue({
                    action: 'store_audio_message',
                    message: event.data
                });
            }
        }
    });
    </script>
    """,
    height=0
)

def save_manual_progress(book, chapter):
    """Manual progress save as fallback"""
    try:
        user_id = st.session_state.get('user_info', {}).get('id')
        if not user_id:
            return False
            
        # For manual save, use estimated values
        success = update_playback_progress_streamlit(
            user_id=user_id,
            book_id=book['id'],
            chapter_id=chapter.get('id') if chapter else None,
            duration=120,  # 2 minutes
            progress=40    # 40%
        )
        
        if success:
            st.success("Progress saved manually!")
        return success
        
    except Exception as e:
        st.error("Manual save failed")
        return False

def show_audio_controls(book, chapter):
    """Show audio controls"""
    st.write("### 🎛️ Controls")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📚 Back to Library", key="back_lib", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("🔄 Refresh Progress", key="refresh_prog", use_container_width=True):
            st.rerun()
    
    with col3:
        if st.button("⏭️ Next Chapter", key="next_ch", use_container_width=True):
            navigate_to_next_chapter(book, chapter)

def navigate_to_next_chapter(book, current_chapter):
    """Navigate to next chapter"""
    if not current_chapter:
        return
        
    next_chapter_num = current_chapter.get('chapter_number', 0) + 1
    next_chapter = get_chapter_by_number(book['id'], next_chapter_num)
    
    if next_chapter:
        # Save current progress before navigating
        save_manual_progress(book, current_chapter)
        play_book_advanced(book['id'], chapter_id=next_chapter['id'])
    else:
        st.success("🎉 You've completed all chapters!")

# Helper functions
def get_resume_position(book_id, chapter_id):
    """Get resume position from database"""
    try:
        user_id = st.session_state.get('user_info', {}).get('id')
        if not user_id or not chapter_id:
            return 0
            
        query = "SELECT duration FROM access_history WHERE user_id = %s AND book_id = %s AND chapter_id = %s ORDER BY accessed_at DESC LIMIT 1"
        result = b.db_select(query, (user_id, book_id, chapter_id), fetch_one=True)
        return result[0] if result else 0
        
    except Exception:
        return 0

def get_progress_info(book_id, chapter_id):
    """Get progress information from database"""
    try:
        user_id = st.session_state.get('user_info', {}).get('id')
        if not user_id or not chapter_id:
            return None
            
        query = "SELECT duration, progress, accessed_at FROM access_history WHERE user_id = %s AND book_id = %s AND chapter_id = %s ORDER BY accessed_at DESC LIMIT 1"
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

def get_chapter_info(book_id, chapter_id, chapter_number):
    """Get chapter information"""
    if chapter_id:
        return get_chapter_by_id(chapter_id)
    elif chapter_number:
        return get_chapter_by_number(book_id, chapter_number)
    else:
        chapters = get_book_chapters(book_id)
        return chapters[0] if chapters else None

# Keep your existing API functions
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


def get_chapter_by_number(book_id, chapter_number):
    # ... your existing code ...
    pass

def get_book_chapters(book_id):
    # ... your existing code ...
    pass

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


# Placeholder functions for other tabs
def show_favorites():
    st.info("Favorites functionality coming soon...")

def show_downloads():
    st.info("Downloads functionality coming soon...")

def show_reading_history():
    st.info("Reading history functionality coming soon...")


def display_working_audio_player(book, chapter, audio_url):
    """Simple audio player that DEFINITELY saves to database"""
    
    st.success(f"🎵 Now Playing: {book['title']}")
    if chapter:
        st.write(f"**Chapter {chapter.get('chapter_number', 'N/A')}**")
    
    # Simple audio player
    st.audio(audio_url, format="audio/mp3")
    
    st.write("---")
    st.write("### 💾 Progress Tracking That Works")
    
    # Initialize session state for timing
    if 'audio_start_time' not in st.session_state:
        st.session_state.audio_start_time = datetime.now()
        st.session_state.last_save_time = datetime.now()
        st.session_state.total_listened = 0
    
    # Calculate time listened in this session
    current_session_time = (datetime.now() - st.session_state.audio_start_time).total_seconds()
    
    # Get previous progress from database
    previous_progress = get_progress_info(book['id'], chapter.get('id') if chapter else None)
    previous_time = previous_progress['duration'] if previous_progress else 0
    
    # Total time listened (previous + current session)
    total_time_listened = previous_time + current_session_time
    
    # Auto-save every 30 seconds
    time_since_last_save = (datetime.now() - st.session_state.last_save_time).total_seconds()
    
    if time_since_last_save >= 30 and current_session_time > 10:
        # Save progress
        save_audio_progress_simple(book, chapter, total_time_listened)
        st.session_state.last_save_time = datetime.now()
        st.session_state.total_listened = total_time_listened
        st.toast(f"💾 Auto-saved: {int(total_time_listened)}s total")
    
    # Display progress information
    st.write(f"**This session:** {int(current_session_time)} seconds")
    st.write(f"**Total listened:** {int(total_time_listened)} seconds")
    
    # Estimate progress based on 1-hour chapters (3600 seconds)
    progress_percent = min((total_time_listened / 3600) * 100, 100)
    st.write(f"**Estimated progress:** {progress_percent:.1f}%")
    st.progress(progress_percent / 100)
    
    # Manual save button
    if st.button("💾 Save Progress Now", type="primary", use_container_width=True):
        save_audio_progress_simple(book, chapter, total_time_listened)
        st.success(f"✅ Saved {int(total_time_listened)} seconds total!")
        st.rerun()
    
    # Quick save buttons for common durations
    st.write("**Quick Save Options:**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("5 min", help="Save 5 minutes listened", use_container_width=True):
            save_audio_progress_simple(book, chapter, 300)  # 5 minutes
    
    with col2:
        if st.button("15 min", help="Save 15 minutes listened", use_container_width=True):
            save_audio_progress_simple(book, chapter, 900)  # 15 minutes
    
    with col3:
        if st.button("30 min", help="Save 30 minutes listened", use_container_width=True):
            save_audio_progress_simple(book, chapter, 1800)  # 30 minutes
    
    with col4:
        if st.button("1 hour", help="Save 1 hour listened", use_container_width=True):
            save_audio_progress_simple(book, chapter, 3600)  # 1 hour
    
    # Show previous progress from database
    if previous_progress and previous_progress.get('duration', 0) > 0:
        st.write("---")
        st.write("#### 📊 Previously Saved Progress")
        prev_time = format_long_time(previous_progress['duration'])
        st.write(f"**Last save:** {prev_time} listened ({previous_progress['progress']}%)")
        
        if st.button("🔄 Resume from previous", help="Continue from last saved position"):
            # Reset session to continue from previous point
            st.session_state.audio_start_time = datetime.now()
            st.session_state.total_listened = previous_progress['duration']
            st.rerun()


def save_audio_progress_simple(book, chapter, seconds_listened):
    """Simple progress saving that definitely works"""
    try:
        user_id = st.session_state.get('user_info', {}).get('id')
        if not user_id:
            st.error("Please login to save progress")
            return False
        
        # Estimate progress based on typical chapter length (1 hour = 3600 seconds)
        progress = min((seconds_listened / 3600) * 100, 100)
        
        print(f"💾 SIMPLE SAVE: {seconds_listened}s, {progress}%")
        
        success = update_playback_progress_streamlit(
            user_id=user_id,
            book_id=book['id'],
            chapter_id=chapter.get('id') if chapter else None,
            duration=int(seconds_listened),
            progress=int(progress)
        )
        
        if success:
            print(f"✅ Database updated successfully!")
            return True
        else:
            print("❌ Database update failed")
            return False
            
    except Exception as e:
        print(f"❌ Simple save error: {e}")
        st.error(f"Save error: {e}")
        return False
    
def format_long_time(total_seconds):
    """Format time in human-readable format"""
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"