# streamlit_app/user/library.py
import streamlit as st
from components.helpers import format_date
from config import API_URL, DEBUG
from flask import Flask, jsonify, request
# from flask import Flask, jsonify, request 
# import config 
# import Flask, jsonify, request
# from flask import Flask, jsonify, request
import requests
# import time
from datetime import datetime
import traceback


######## my_library ########
def my_library():
    """User's personal library main function"""
    if 'playback_state' not in st.session_state:
        st.session_state.playback_state = {
            'is_playing': False,
            'current_time': 0,
            'total_duration': 300,
            'progress_percent': 0.0,
            'last_update': None,
            'last_progress_update': None
        }

    if 'currently_playing' not in st.session_state:
        st.session_state.currently_playing = None

    st.header("📖 My Personal Library")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Recently Played", "Favorites", "Downloads", "Reading History"])
    
    with tab1:
        show_recently_played()
    with tab2:
        show_favorites()
    with tab3:
        show_downloads()
    with tab4:
        show_reading_history()

######## my_library - show_recently_played ########
def show_recently_played():
    """Show recently played/accessed books"""
    from .browse import show_book_recommendations

    # Initialize session state
    if 'playback_state' not in st.session_state:
        st.session_state.playback_state = {
            'is_playing': False,
            'current_time': 0,
            'total_duration': 300,
            'progress_percent': 0.0
        }
    
    st.subheader("🎵 Recently Played")
    
    try:
        user_id = st.session_state.get('user_id')
        if not user_id:
            st.info("Please login to view your listening history")
            return
        
        recent_books = get_recently_played(user_id, limit=10)

        if recent_books:
            for i, book in enumerate(recent_books):
                try:
                    display_recent_book(book, index=i)
                except Exception as e:
                    st.error(f"Error displaying book: {str(e)}")
                    continue  # Continue with next book even if one fails
                
            # Quick actions
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Refresh", key="refresh_recent_unique", use_container_width=True):
                    st.rerun()
            with col2:
                if st.button("🗑️ Clear History", key="clear_history_unique", use_container_width=True):
                    if clear_recent_history(user_id):
                        st.success("History cleared!")
                        st.rerun()
                    
        else:
            # Fallback: Show popular books with WORKING play buttons
            st.info("You haven't played any books yet. Here are some popular choices to get started:")
            show_book_recommendations()
            
    except Exception as e:
        st.error(f"Error loading your history: {str(e)}")
        if DEBUG:
            st.error(f"Detailed error: {traceback.format_exc()}")
        # Fallback to recommendations
        # show_book_recommendations()

def clear_recent_history(user_id):
    """Clear user's recent history"""
    try:
        query = "DELETE FROM access_history WHERE user_id = %s"
        result = b.db_update(query, (user_id,))
        return result is not None
    except Exception as e:
        print(f"❌ Error clearing history: {str(e)}")
        return False

# def show_recently_played():
#     """Show recently played/accessed books"""
#     from .browse import show_book_recommendations
#     st.subheader("🎵 Recently Played")
    
#     try:
#         user_id = st.session_state.get('user_id')
#         print(f"user-id = {user_id}")
#         if not user_id:
#             st.info("Please login to view your listening history")
#             return
        
#         recent_books = get_recently_played(user_id, limit=10)
#         print(f"recent_books = {recent_books}")

#         if recent_books:
#             # Show actual recently played books with play buttons
#             for book in recent_books:
#                 display_recent_book(book)
                
#             # Quick actions
#             st.markdown("---")
#             col1, col2 = st.columns(2)
#             with col1:
#                 if st.button("🔄 Refresh", use_container_width=True):
#                     st.rerun()
#             with col2:
#                 if st.button("🗑️ Clear History", use_container_width=True):
#                     if clear_recent_history(user_id):
#                         st.success("History cleared!")
#                         st.rerun()
                    
#         else:
#             # Fallback: Show popular books with WORKING play buttons
#             st.info("You haven't played any books yet. Here are some popular choices to get started:")
#             show_book_recommendations()
            
    # except Exception as e:
    #     st.error(f"Error loading your history: {str(e)}")
    #     # Fallback to recommendations
    #     show_book_recommendations()


######## my_library - show_recently_played - show_recently_played ########
# Database helper functions (to be implemented)

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
    
import time
import random
def generate_unique_key(book, index):
    """Generate a truly unique key for widgets"""
    book_id = book['id']
    chapter_id = book.get('chapter_id', 0)
    last_played = book.get('last_played', '')
    timestamp = int(time.time() * 1000)  # Current timestamp in milliseconds
    random_suffix = random.randint(1000, 9999)  # Random number
    
    return f"recent_{book_id}_{chapter_id}_{hash(last_played)}_{index}_{timestamp}_{random_suffix}"
######## my_library - show_recently_played - display_recent_book ########
def display_recent_book(book, index=0):
    """Display a recently played book with unique keys"""
    # Create simple unique key using index and book data
    book_id = book['id']
    chapter_id = book.get('chapter_id', 0)
    unique_key = f"recent_{book_id}_{chapter_id}_{index}"
    
    with st.container():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.write(f"**📖 {book['title']}** by {book['author']}")
            
            # Format last played time
            last_played = book.get('last_played', '')
            if last_played:
                st.write(f"**Last played:** {last_played}")
            
            # Show progress if available (from database)
            # Show progress if available (from database)
            progress = book.get('progress', 0)
            if progress > 0:
                st.progress(progress / 100)
                st.write(f"**Progress:** {progress}%")
            else:
                st.write(f"**Progress:** {progress}% (not started)")

            # progress = book.get('progress', 0)
            # if progress > 0:
            #     st.progress(progress / 100)
            #     st.write(f"**Progress:** {progress}%")
            
            # Show duration if available
            duration = book.get('duration', 0)
            if duration > 0:
                minutes = duration // 60
                seconds = duration % 60
                st.write(f"**Time listened:** {minutes}:{seconds:02d}")
            else:
                st.write("**Time listened:** 0:00")
            # duration = book.get('duration', 0)
            # if duration > 0:
            #     minutes = duration // 60
            #     seconds = duration % 60
            #     st.write(f"**Time listened:** {minutes}:{seconds:02d}")
            
            # Show current chapter
            current_chapter = book.get('current_chapter', '')
            chapter_number = book.get('chapter_number', '')
            if current_chapter or chapter_number:
                display_text = ""
                if chapter_number:
                    display_text += f"Chapter {chapter_number}"
                if current_chapter:
                    if display_text:
                        display_text += f" - {current_chapter}"
                    else:
                        display_text = current_chapter
                st.write(f"**Current chapter:** {display_text}")
        
        with col2:
            user_info = st.session_state.get('user_info', {})
            user_id = user_info.get('id')
            
            # Simple button without form
            if st.button("▶️ Continue", key=unique_key, use_container_width=True):
                if user_id:
                    # Get progress from the book data (database)
                    book_progress = book.get('progress', 0)
                    book_duration = book.get('duration', 0)
                    
                    print(f"🔍 Continue button clicked:")
                    print(f"   User ID: {user_id}")
                    print(f"   Book ID: {book_id}") 
                    print(f"   Chapter ID: {chapter_id}")
                    print(f"   Book Progress: {book_progress}%")
                    print(f"   Duration: {book_duration}s")
                    
                    # If we have progress, use it to set the playback position
                    if book_progress > 0 and book_duration == 0:
                        # Estimate duration based on progress (assuming 5min total)
                        book_duration = int((book_progress / 100) * 300)
                        print(f"   Estimated Duration: {book_duration}s")

                    # Update playback progress
                    success = update_playback_progress_streamlit(
                        user_id, 
                        book_id, 
                        chapter_id, 
                        book_duration, 
                        book_progress
                    )
                    
                    if success:
                        st.success("Resuming playback...")
                        # Use a different approach to play the book without conflicting buttons
                        
                        # Set the playback state to resume from the correct position
                        st.session_state.playback_state = {
                            'is_playing': True,
                            'current_time': book_duration,  # Start from saved position
                            'total_duration': 300,
                            'progress_percent': book_progress,  # Use actual progress
                            'last_update': datetime.now(),
                            'last_progress_update': datetime.now(),
                            'last_saved_time': book_duration
                        }

                        st.session_state.playback_start_time = datetime.now()
                        st.session_state.playback_accumulated_time = book_duration
                        st.session_state.playback_last_update = datetime.now()
                        play_book_safe(book_id, chapter_id=chapter_id)
                    else:
                        st.error("Failed to resume playback")
                else:
                    st.error("Please login to continue playback")
        
        st.markdown("---")

def play_book_safe(book_id, chapter_id=None, chapter_number=None):
    """Safe version of play_book with auto-saving"""
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
        
        # If no specific chapter, get the first chapter
        if not chapter_id and not chapter_number:
            chapters = get_book_chapters(book_id)
            if chapters:
                chapter = chapters[0]
                chapter_id = chapter['id']
                chapter_number = chapter['chapter_number']
            else:
                st.error("No chapters available for this book")
                return
        
        # Get chapter information
        if chapter_number and not chapter_id:
            chapter = get_chapter_by_number(book_id, chapter_number)
            if chapter:
                chapter_id = chapter['id']
            else:
                st.error("Chapter not found!")
                return
        
        chapter = get_chapter_by_id(chapter_id) if chapter_id else None
        if not chapter:
            st.error("Chapter not found!")
            return
        
        # Generate audio URL
        chapter_title = chapter.get('title', f'chapter_{chapter.get("chapter_number", "1")}')
        audio_url = get_signed_audio_url(book_id, chapter_title)
        
        if not audio_url:
            st.error("No audio file available for this content")
            return
        
        # Update session state
        st.session_state.currently_playing = {
            'book_id': book_id,
            'chapter_id': chapter_id,
            'book_title': book['title'],
            'chapter_title': chapter.get('title', f'Chapter {chapter.get("chapter_number", "N/A")}'),
            'chapter_number': chapter.get('chapter_number', 0),
            'audio_url': audio_url,
            'start_time': datetime.now()
        }
        
        # DON'T reset playback state if it already exists (for resume functionality)
        if 'playback_state' not in st.session_state:
            st.session_state.playback_state = {
                'is_playing': False,
                'current_time': 0,
                'total_duration': 300,
                'progress_percent': 0,
                'last_update': datetime.now(),
                'last_progress_update': None,
                'last_saved_time': 0
            }
        else:
            # Keep the existing playback state (for resume)
            print(f"🎯 Resuming from: {st.session_state.playback_state['current_time']}s")
        
        # Initialize playback tracking variables if they don't exist
        if 'playback_start_time' not in st.session_state:
            st.session_state.playback_start_time = None
            st.session_state.playback_accumulated_time = 0
            st.session_state.playback_last_update = datetime.now()
        
        # Display the audio player
        display_audio_player_simple(book, chapter, audio_url)
        
    except Exception as e:
        st.error(f"Error playing book: {str(e)}")


def display_audio_player_safe(book, chapter, audio_url):
    """Audio player that automatically saves progress"""
    st.success(f"🎵 Now Playing: {book['title']}" + 
              (f" - Chapter {chapter['chapter_number']}" if chapter else ""))
    
    # Audio player
    st.audio(audio_url, format="audio/mp3")
    
    # Progress tracking UI
    if 'playback_state' in st.session_state:
        playback_state = st.session_state.playback_state
        
        # Store previous time to detect changes
        previous_time = playback_state.get('current_time', 0)
        
        # Progress slider with callback
        current_time = st.slider(
            "Progress",
            min_value=0,
            max_value=playback_state.get('total_duration', 300),
            value=playback_state.get('current_time', 0),
            format="%d seconds",
            key="audio_progress_auto_save",
            on_change=lambda: auto_save_progress()  # Auto-save when slider changes
        )
        
        # Update playback state
        playback_state['current_time'] = current_time
        if playback_state['total_duration'] > 0:
            playback_state['progress_percent'] = (current_time / playback_state['total_duration']) * 100
        
        # Auto-save if time changed significantly (more than 5 seconds)
        if abs(current_time - previous_time) >= 5:
            auto_save_progress()
        
        # Display time and progress
        col_time, col_progress = st.columns(2)
        with col_time:
            st.write(f"**Time:** {format_time(playback_state['current_time'])} / {format_time(playback_state['total_duration'])}")
        with col_progress:
            progress_percent = playback_state.get('progress_percent', 0)
            st.write(f"**Progress:** {progress_percent:.1f}%")
            if progress_percent > 0:
                st.progress(progress_percent / 100)
    
    # Auto-save function
    def auto_save_progress():
        """Automatically save progress when significant changes occur"""
        if update_playback_progress():
            print("✅ Progress auto-saved")
        else:
            print("❌ Failed to auto-save progress")
    
    # Playback controls with auto-save
    if chapter:
        st.write("**Playback Controls:**")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("⏮️ Previous", key="prev_chapter_auto", use_container_width=True):
                # Save progress before changing chapter
                update_playback_progress()
                play_previous_chapter_safe(book['id'], chapter['chapter_number'])
        
        with col2:
            play_text = "⏸️ Pause" if playback_state.get('is_playing', False) else "▶️ Play"
            if st.button(play_text, key="play_pause_auto", use_container_width=True):
                # Save progress when pausing
                if playback_state.get('is_playing', False):  # If currently playing, we're about to pause
                    update_playback_progress()
                
                playback_state['is_playing'] = not playback_state.get('is_playing', False)
                st.rerun()
        
        with col3:
            if st.button("⏭️ Next", key="next_chapter_auto", use_container_width=True):
                # Save progress before changing chapter
                update_playback_progress()
                play_next_chapter_safe(book['id'], chapter['chapter_number'])
    
    # Manual save progress button
    if st.button("💾 Save Progress Now", key="save_progress_manual", use_container_width=True):
        if update_playback_progress():
            st.success("✅ Progress saved to database!")
            # Force a rerun to show updated progress
            st.rerun()
        else:
            st.error("❌ Failed to save progress")
    
    # Add a debug section to show current state
    if DEBUG:
        with st.expander("🔧 Debug Info"):
            st.write("**Session State:**")
            st.json(st.session_state.get('playback_state', {}))
            st.write("**Currently Playing:**")
            st.json(st.session_state.get('currently_playing', {}))
            
            # Test database connection
            if st.button("Test Database Update"):
                test_result = update_playback_progress()
                st.write(f"Test result: {test_result}")

# def display_audio_player_safe(book, chapter, audio_url):
#     """Audio player that respects resume position"""
#     st.success(f"🎵 Now Playing: {book['title']}" + 
#               (f" - Chapter {chapter['chapter_number']}" if chapter else ""))
    
#     # Audio player
#     st.audio(audio_url, format="audio/mp3")
    
#     # Progress tracking UI - start from resumed position
#     if 'playback_state' in st.session_state:
#         playback_state = st.session_state.playback_state
        
#         # Start from the resumed position, not from 0
#         initial_time = playback_state.get('current_time', 0)
        
#         # Progress slider
#         current_time = st.slider(
#             "Progress",
#             min_value=0,
#             max_value=playback_state.get('total_duration', 300),
#             value=initial_time,  # Start from resumed position
#             format="%d seconds",
#             key="audio_progress_resume"
#         )
        
#         # Update playback state
#         playback_state['current_time'] = current_time
#         if playback_state['total_duration'] > 0:
#             playback_state['progress_percent'] = (current_time / playback_state['total_duration']) * 100
        
#         # Display time and progress
#         col_time, col_progress = st.columns(2)
#         with col_time:
#             st.write(f"**Time:** {format_time(playback_state['current_time'])} / {format_time(playback_state['total_duration'])}")
#         with col_progress:
#             progress_percent = playback_state.get('progress_percent', 0)
#             st.write(f"**Progress:** {progress_percent:.1f}%")
#             if progress_percent > 0:
#                 st.progress(progress_percent / 100)
    
#     # Playback controls
#     if chapter:
#         st.write("**Playback Controls:**")
        
#         col1, col2, col3 = st.columns([1, 1, 1])
        
#         with col1:
#             if st.button("⏮️ Previous", key="prev_chapter_resume", use_container_width=True):
#                 play_previous_chapter_safe(book['id'], chapter['chapter_number'])
        
#         with col2:
#             play_text = "⏸️ Pause" if st.session_state.playback_state.get('is_playing', False) else "▶️ Play"
#             if st.button(play_text, key="play_pause_resume", use_container_width=True):
#                 st.session_state.playback_state['is_playing'] = not st.session_state.playback_state.get('is_playing', False)
#                 st.rerun()
        
#         with col3:
#             if st.button("⏭️ Next", key="next_chapter_resume", use_container_width=True):
#                 play_next_chapter_safe(book['id'], chapter['chapter_number'])
    
#     # Save progress button
#     if st.button("💾 Save Progress", key="save_progress_resume", use_container_width=True):
#         if update_playback_progress():
#             st.success("Progress saved!")
#         else:
#             st.error("Failed to save progress")

# def display_audio_player_safe(book, chapter, audio_url):
#     """Safe audio player display without button conflicts"""
#     st.success(f"🎵 Now Playing: {book['title']}" + 
#               (f" - Chapter {chapter['chapter_number']}" if chapter else ""))
    
#     # Audio player
#     st.audio(audio_url, format="audio/mp3")
    
#     # Progress tracking UI
#     if 'playback_state' in st.session_state:
#         playback_state = st.session_state.playback_state
        
#         # Progress slider with unique key
#         current_time = st.slider(
#             "Progress",
#             min_value=0,
#             max_value=playback_state.get('total_duration', 300),
#             value=playback_state.get('current_time', 0),
#             format="%d seconds",
#             key="audio_progress_slider_safe"  # Unique key
#         )
        
#         # Update playback state
#         playback_state['current_time'] = current_time
#         if playback_state['total_duration'] > 0:
#             playback_state['progress_percent'] = (current_time / playback_state['total_duration']) * 100
        
#         # Display time and progress
#         col_time, col_progress = st.columns(2)
#         with col_time:
#             st.write(f"**Time:** {format_time(playback_state['current_time'])} / {format_time(playback_state['total_duration'])}")
#         with col_progress:
#             st.write(f"**Progress:** {playback_state.get('progress_percent', 0):.1f}%")
#             if playback_state.get('progress_percent', 0) > 0:
#                 st.progress(playback_state['progress_percent'] / 100)
    
#     # Simple playback controls without nested buttons
#     if chapter:
#         st.write("**Playback Controls:**")
        
#         col1, col2, col3 = st.columns([1, 1, 1])
        
#         with col1:
#             if st.button("⏮️ Previous", key="prev_chapter_safe", use_container_width=True):
#                 play_previous_chapter_safe(book['id'], chapter['chapter_number'])
        
#         with col2:
#             play_text = "⏸️ Pause" if st.session_state.playback_state.get('is_playing', False) else "▶️ Play"
#             if st.button(play_text, key="play_pause_safe", use_container_width=True):
#                 st.session_state.playback_state['is_playing'] = not st.session_state.playback_state.get('is_playing', False)
#                 st.rerun()
        
#         with col3:
#             if st.button("⏭️ Next", key="next_chapter_safe", use_container_width=True):
#                 play_next_chapter_safe(book['id'], chapter['chapter_number'])
    
#     # Manual progress update button with unique key
#     if st.button("💾 Save Progress", key="save_progress_safe", use_container_width=True):
#         if update_playback_progress():
#             st.success("Progress saved!")
#         else:
#             st.error("Failed to save progress")
    
#     # Download button with unique key
#     try:
#         audio_response = requests.get(audio_url, timeout=30)
#         if audio_response.status_code == 200:
#             file_name = f"{sanitize_filename(book['title'])}"
#             if chapter:
#                 file_name += f"_Chapter_{chapter['chapter_number']}"
#             file_name += ".mp3"
            
#             st.download_button(
#                 label="📥 Download MP3",
#                 data=audio_response.content,
#                 file_name=file_name,
#                 mime="audio/mp3",
#                 key="download_audio_safe",  # Unique key
#                 use_container_width=True
#             )
#         else:
#             st.warning("Download temporarily unavailable")
#     except Exception as e:
#         st.warning(f"Download error: {str(e)}")

def play_previous_chapter_safe(book_id, current_chapter_number):
    """Safe version of previous chapter navigation"""
    # Finalize current playback
    finalize_playback()
    
    previous_chapter = get_chapter_by_number(book_id, current_chapter_number - 1)
    if previous_chapter:
        play_book_safe(book_id, chapter_id=previous_chapter['id'])
    else:
        st.warning("No previous chapter available")

def play_next_chapter_safe(book_id, current_chapter_number):
    """Safe version of next chapter navigation"""
    # Finalize current playback
    finalize_playback()
    
    next_chapter = get_chapter_by_number(book_id, current_chapter_number + 1)
    if next_chapter:
        play_book_safe(book_id, chapter_id=next_chapter['id'])
    else:
        st.warning("No next chapter available")

# def display_recent_book(book, index=0):
#     """Display a recently played book with unique keys"""
#     # Create unique keys using book ID, chapter ID, and index
#     book_id = book['id']
#     chapter_id = book.get('chapter_id', 0)
#     last_played = book.get('last_played', '')
#     progress = book.get('progress', 0)
#     duration = book.get('duration', 0)

#     key_data = f"{book_id}_{chapter_id}_{last_played}_{progress}_{duration}_{index}"
#     key_hash = hash(key_data) & 0xFFFFFFFF  # Ensure positive hash

#     unique_key = f"recent_{key_hash}_{index}"
#     # unique_key = f"{book_id}_{chapter_id}_{index}"
    
#     # unique_key = generate_unique_key(book, index)

#     with st.container():
#         col1, col2 = st.columns([4, 1])
        
#         with col1:
#             st.write(f"**📖 {book['title']}** by {book['author']}")
            
#             # Format last played time
#             last_played = book.get('last_played', '')
#             if last_played:
#                 st.write(f"**Last played:** {last_played}")
            
#             # Show progress if available
#             progress = book.get('progress', 0)
#             if progress > 0:
#                 st.progress(progress / 100)
#                 st.write(f"**Progress:** {progress}%")
            
#             # Show duration if available
#             if duration > 0:
#                 minutes = duration // 60
#                 seconds = duration % 60
#                 st.write(f"**Time listened:** {minutes}:{seconds:02d}")

#             # Show current chapter
#             current_chapter = book.get('current_chapter', '')
#             chapter_number = book.get('chapter_number', '')
#             if current_chapter or chapter_number:
#                 display_text = ""
#                 if chapter_number:
#                     display_text += f"Chapter {chapter_number}"
#                 if current_chapter:
#                     if display_text:
#                         display_text += f" - {current_chapter}"
#                     else:
#                         display_text = current_chapter
#                 st.write(f"**Current chapter:** {display_text}")
        
#         with col2:
#             user_info = st.session_state.get('user_info', {})
#             user_id = user_info.get('id')
            
#             if user_id:
#                 # Get progress from the book data (database)
#                 book_progress = book.get('progress', 0)
#                 # Use actual duration from database
#                 book_duration = book.get('duration', 0)
                
#                 # Use a form to handle the button click properly
#                 with st.form(key=f"form_{unique_key}"):
#                     if st.form_submit_button("▶️ Continue", use_container_width=True):
#                         print(f"🔍 Continue button clicked:")
#                         print(f"   User ID: {user_id}")
#                         print(f"   Book ID: {book_id}") 
#                         print(f"   Chapter ID: {chapter_id}")
#                         print(f"   Book Progress: {book_progress}%")
#                         print(f"   Duration: {book_duration}s")
                        
#                         # First update the playback progress
#                         success = update_playback_progress_streamlit(
#                             user_id, 
#                             book_id, 
#                             chapter_id, 
#                             book_duration, 
#                             book_progress
#                         )
                        
#                         if success:
#                             st.success("Resuming playback...")
#                             # Start playing the book
#                             play_book(book_id, chapter_id=chapter_id)
#                         else:
#                             st.error("Failed to resume playback")
#             else:
#                 # For disabled state, use a different approach
#                 st.write("")  # Spacer
#                 st.button("▶️ Continue", key=f"disabled_{unique_key}", disabled=True, use_container_width=True)
        
#         st.markdown("---")

# def display_recent_book(book):
#     """Display a recently played book with play buttons"""
#     with st.expander(f"📖 {book['title']} by {book['author']}", expanded=False):
#         col1, col2 = st.columns([3, 1])
        
#         with col1:
#             st.write(f"**Last played:** {format_date(book['last_played'])}")
#             st.write(f"**Progress:** {book.get('progress', '0')}%")
#             if book.get('current_chapter'):
#                 st.write(f"**Current chapter:** {book['current_chapter']}")
        
#         with col2:
#             # ✅ Continue playing from where they left off
#             if st.button("▶️ Continue", key=f"cont_{book['id']}", use_container_width=True):
#                 play_book(book['id'], chapter_id=book.get('current_chapter_id'))
            
#             # ✅ Start from beginning
#             if st.button("📖 Start Over", key=f"start_{book['id']}", use_container_width=True):
#                 play_book(book['id'])

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


######## my_library - show_recently_played - play_book ########
def play_book(book_id, chapter_id=None, chapter_number=None):
    """Main function to handle book/chapter playback"""
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
        
        # If no specific chapter, get the first chapter
        if not chapter_id and not chapter_number:
            chapters = get_book_chapters(book_id)
            if chapters:
                chapter = chapters[0]
                chapter_id = chapter['id']
                chapter_number = chapter['chapter_number']
            else:
                st.error("No chapters available for this book")
                return
        
        # Get chapter information if only number is provided
        if chapter_number and not chapter_id:
            chapter = get_chapter_by_number(book_id, chapter_number)
            if chapter:
                chapter_id = chapter['id']
            else:
                st.error("Chapter not found!")
                return
        
        # Get full chapter details
        chapter = get_chapter_by_id(chapter_id) if chapter_id else None
        if not chapter:
            st.error("Chapter not found!")
            return
        
        # Generate audio URL using your existing function
        chapter_title = chapter.get('title', f'chapter_{chapter.get("chapter_number", "1")}')
        audio_url = get_signed_audio_url(book_id, chapter_title)
        
        if not audio_url:
            st.error("No audio file available for this content")
            return
        
        # Record initial play
        record_audio_play(
        # record_audio_play_streamlit(
            user_id=user_id,
            book_id=book_id,
            chapter_id=chapter_id,
            duration=0,
            progress=0
        )
        
        # Update session state
        st.session_state.currently_playing = {
            'book_id': book_id,
            'chapter_id': chapter_id,
            'book_title': book['title'],
            'chapter_title': chapter.get('title', f'Chapter {chapter.get("chapter_number", "N/A")}'),
            'chapter_number': chapter.get('chapter_number', 0),
            'audio_url': audio_url,
            'start_time': datetime.now()
        }
        
        # Reset playback state for new playback
        st.session_state.playback_state = {
            'is_playing': False,
            'current_time': 0,
            'total_duration': 300,
            'progress_percent': 0,
            'last_update': None,
            'last_progress_update': None
        }
        
        # Display the audio player
        display_audio_player(book, chapter, audio_url)
        
    except Exception as e:
        st.error(f"Error playing book: {str(e)}")

# def play_book(book_id, chapter_id=None, chapter_number=None):
#     """Main function to handle book/chapter playback"""
#     try:
#         user_id = st.session_state.get('user_id')
#         if not user_id:
#             st.error("Please login to play audio books")
#             return
        
#         # Get book information
#         book = get_book_by_id(book_id)
#         if not book:
#             st.error("Book not found!")
#             return
        
#         # If no specific chapter, get the first chapter
#         if not chapter_id and not chapter_number:
#             chapters = get_book_chapters(book_id)
#             if chapters:
#                 chapter = chapters[0]
#                 chapter_id = chapter['id']
#                 chapter_number = chapter['chapter_number']
#             else:
#                 st.error("No chapters available for this book")
#                 return
        
#         # Get chapter information if only number is provided
#         if chapter_number and not chapter_id:
#             chapter = get_chapter_by_number(book_id, chapter_number)
#             if chapter:
#                 chapter_id = chapter['id']
#             else:
#                 st.error("Chapter not found!")
#                 return
        
#         # Get full chapter details
#         chapter = get_chapter_by_id(chapter_id) if chapter_id else None
#         if not chapter:
#             st.error("Chapter not found!")
#             return
        
#         # Record this play in access history
#         record_audio_play(
#             user_id=user_id,
#             book_id=book_id,
#             chapter_id=chapter_id,
#             duration=0,  # Will update with actual duration later
#             progress=0   # Will update with progress later
#         )
        
#         # Generate audio URL
#         audio_url = get_signed_audio_url(book_id, chapter['title'])
#         if not audio_url:
#             st.error("Could not generate audio URL")
#             return
        
#         # Display the audio player
#         display_audio_player(book, chapter, audio_url)
        
#         # Update session state to reflect current playback
#         st.session_state.currently_playing = {
#             'book_id': book_id,
#             'chapter_id': chapter_id,
#             'book_title': book['title'],
#             'chapter_title': chapter['title'],
#             'chapter_number': chapter['chapter_number'],
#             'audio_url': audio_url,
#             'start_time': datetime.now()
#         }
        
#     except Exception as e:
#         st.error(f"Error playing book: {str(e)}")


######## my_library - show_recently_played - get_book_by_id ########
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
                return get_sample_book()
        elif response.status_code == 404:
            st.error("Book not found")
            return get_sample_book()
        else:
            st.error(f"Failed to fetch book: {response.status_code}")
            return get_sample_book()
            
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return get_sample_book()
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return get_sample_book()

def get_sample_book():
    """Return sample book data for testing"""
    return {
        'id': 1,
        'title': 'Sample Book Title',
        'author': 'Sample Author',
        'description': 'This is a sample book description for testing purposes.',
        'category_id': 1,
        'category_name': 'Fiction',
        'language': 'English',
        'duration': '05:30:00',
        'cover_image': 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=300',
        'audio_url': 'https://example.com/sample-audio.mp3',
        'published_year': 2024,
        'isbn': '978-3-16-148410-0',
        'rating': 4.5,
        'total_chapters': 12,
        'created_at': '2024-01-01 10:00:00'
    }
######## my_library - show_recently_played - get_book_chapters ########
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


######## my_library - show_recently_played - get_chapter_by_number ########
def get_chapter_by_number(book_id, chapter_number):
    """Get chapter by number via API"""
    try:
        response = requests.get(
            f"{API_URL}/api/chapter/by-number",
            params={
                "book_id": book_id,
                "chapter_number": chapter_number
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('chapter')
        return None
        
    except Exception as e:
        print(f"❌ Error getting chapter: {str(e)}")
        return None


######## my_library - show_recently_played - get_chapter_by_id ########
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

######## my_library - record_audio_play ########
######## browse_books - record_audio_play ########
def record_audio_play(user_id, book_id, chapter_id=None, duration=0, progress=0):
    """Call Flask API to record audio play"""
    try:
        payload = {
            "user_id": user_id,
            "book_id": book_id,
            "chapter_id": chapter_id,
            "duration": duration,
            "progress": progress
        }

        response = requests.post(
            f"{API_URL}/api/record-play",
            json=payload,
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error calling record API: {str(e)}")
        return False


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


######## my_library - show_recently_played - display_audio_player ########
def display_audio_player(book, chapter, audio_url):
    """Display audio player with progress tracking"""
    st.success(f"🎵 Now Playing: {book['title']}" + 
              (f" - Chapter {chapter['chapter_number']}" if chapter else ""))
    
    # Audio player
    st.audio(audio_url, format="audio/mp3")
    
    # Progress tracking UI
    if 'playback_state' in st.session_state:
        playback_state = st.session_state.playback_state
        
        # Create a callback function for the slider
        def on_slider_change():
            print("🔄 Slider changed - updating progress")
            current_time = st.session_state.progress_slider
            playback_state['current_time'] = current_time
            if playback_state['total_duration'] > 0:
                playback_state['progress_percent'] = (current_time / playback_state['total_duration']) * 100
            update_playback_progress()

        # Progress slider
        current_time = st.slider(
            "Progress",
            min_value=0,
            max_value=playback_state.get('total_duration', 300),
            value=playback_state.get('current_time', 0),
            # value=50,
            format="%d seconds",
            key="progress_slider",
            # on_change=on_slider_change
        )
        print(f"🔍 Slider value: {current_time}, Stored value: {playback_state['current_time']}")
        print(f"🔍 Before condition - current_time: {current_time}, playback_state['current_time']: {playback_state['current_time']}")
        print(f"🔍 Condition result: {current_time != playback_state['current_time']}")

        print(f"before - update_playback_progress() : {current_time}")
        # Update if slider changed
        # if current_time != playback_state['current_time']:
        print("✅ Condition is TRUE - updating progress")
        playback_state['current_time'] = current_time
        if playback_state['total_duration'] > 0:
            playback_state['progress_percent'] = (current_time / playback_state['total_duration']) * 100
            # playback_state['progress_percent'] = 16.7  # 50/300 * 100
        else:
            print("❌ Condition is FALSE - not updating progress")
        print("after - update_playback_progress()")
        # Update progress in database
        update_playback_progress()
        
        # Display time and progress
        col_time, col_progress = st.columns(2)
        with col_time:
            st.write(f"**Time:** {format_time(playback_state['current_time'])} / {format_time(playback_state['total_duration'])}")
        with col_progress:
            st.write(f"**Progress:** {playback_state.get('progress_percent', 0):.1f}%")
            if playback_state.get('progress_percent', 0) > 0:
                st.progress(current_chapter_progress / 100)  # If progress is 0-100
                st.write(f"Time: {format_time(current_time)} / {format_time(total_duration)}")
                st.write(f"Progress: {current_chapter_progress}%")

                # For the overall book progress - use book progress from database
                st.write(f"Overall Progress: {book_progress}%")
                # st.progress(playback_state['progress_percent'] / 100)
    
    # Playback controls
    if chapter:
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("⏮️ Previous", use_container_width=True):
                play_previous_chapter(book['id'], chapter['chapter_number'])
        
        with col2:
            play_text = "⏸️ Pause" if st.session_state.playback_state.get('is_playing', False) else "▶️ Play"
            if st.button(play_text, use_container_width=True):
                st.session_state.playback_state['is_playing'] = not st.session_state.playback_state.get('is_playing', False)
                st.rerun()
        
        with col3:
            if st.button("⏭️ Next", use_container_width=True):
                play_next_chapter(book['id'], chapter['chapter_number'])
    
    # Manual progress update button
    if st.button("💾 Save Progress", use_container_width=True):
        if update_playback_progress():
            st.success("Progress saved!")
        else:
            st.error("Failed to save progress")
    
    # Download button
    try:
        audio_response = requests.get(audio_url, timeout=30)
        if audio_response.status_code == 200:
            file_name = f"{sanitize_filename(book['title'])}"
            if chapter:
                file_name += f"_Chapter_{chapter['chapter_number']}"
            file_name += ".mp3"
            
            st.download_button(
                label="📥 Download MP3",
                data=audio_response.content,
                file_name=file_name,
                mime="audio/mp3",
                use_container_width=True
            )
        else:
            st.warning("Download temporarily unavailable")
    except Exception as e:
        st.warning(f"Download error: {str(e)}")

def format_time(seconds):
    """Format seconds into MM:SS format"""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

# def display_audio_player(book, chapter, audio_url):
#     """Display audio player with controls"""
#     st.success(f"🎵 Now Playing: {book['title']}" + 
#               (f" - Chapter {chapter['chapter_number']}" if chapter else ""))
    
#     # Audio player
#     st.audio(audio_url, format="audio/mp3")
    
#     # Simple progress display
#     if 'playback_state' in st.session_state:
#         progress = st.session_state.playback_state.get('progress_percent', 0)
#         if progress > 0:
#             st.progress(progress / 100)
#             st.write(f"**Progress:** {progress:.1f}%")
    
#     # Playback controls
#     if chapter:
#         col1, col2, col3 = st.columns([1, 1, 1])
        
#         with col1:
#             if st.button("⏮️ Previous", use_container_width=True):
#                 play_previous_chapter(book['id'], chapter['chapter_number'])
        
#         with col2:
#             play_text = "⏸️ Pause" if st.session_state.playback_state.get('is_playing', False) else "▶️ Play"
#             if st.button(play_text, use_container_width=True):
#                 # Simple toggle without time functions
#                 st.session_state.playback_state['is_playing'] = not st.session_state.playback_state.get('is_playing', False)
#                 st.rerun()
        
#         with col3:
#             if st.button("⏭️ Next", use_container_width=True):
#                 play_next_chapter(book['id'], chapter['chapter_number'])
    
#     # Download button
#     try:
#         audio_response = requests.get(audio_url, timeout=30)
#         if audio_response.status_code == 200:
#             file_name = f"{sanitize_filename(book['title'])}"
#             if chapter:
#                 file_name += f"_Chapter_{chapter['chapter_number']}"
#             file_name += ".mp3"
            
#             st.download_button(
#                 label="📥 Download MP3",
#                 data=audio_response.content,
#                 file_name=file_name,
#                 mime="audio/mp3",
#                 use_container_width=True
#             )
#         else:
#             st.warning("Download temporarily unavailable")
#     except Exception as e:
#         st.warning(f"Download error: {str(e)}")

# def display_audio_player(book, chapter, audio_url):
#     """Display the audio player with controls and progress tracking"""
#     st.success(f"🎵 Now Playing: {book['title']} - Chapter {chapter['chapter_number']}")
    
#     # Initialize playback state if not exists
#     if 'playback_state' not in st.session_state:
#         st.session_state.playback_state = {
#             'is_playing': False,
#             'current_time': 0,
#             'total_duration': 300,  # Default 5 minutes, will be updated from audio
#             'progress_percent': 0,
#             'last_update': None,
#             'last_progress_update': None
#         }
    
#     # Create a container for the audio player
#     player_container = st.container()
    
#     with player_container:
#         # Audio player
#         st.audio(audio_url, format="audio/mp3")
        
#         # Progress tracking UI
#         col_progress1, col_progress2 = st.columns([3, 1])
        
#         with col_progress1:
#             # Progress slider
#             current_time = st.slider(
#                 "Progress",
#                 min_value=0,
#                 max_value=st.session_state.playback_state['total_duration'],
#                 value=st.session_state.playback_state['current_time'],
#                 format="%d seconds",
#                 key="progress_slider",
#                 label_visibility="collapsed"
#             )
            
#             # Update progress if slider changed
#             if current_time != st.session_state.playback_state['current_time']:
#                 st.session_state.playback_state['current_time'] = current_time
#                 st.session_state.playback_state['progress_percent'] = (
#                     current_time / st.session_state.playback_state['total_duration'] * 100
#                     if st.session_state.playback_state['total_duration'] > 0 else 0
#                 )
                
#                 # Update progress in database
#                 update_playback_progress()
        
#         with col_progress2:
#             st.write(
#                 f"{format_time(st.session_state.playback_state['current_time'])} / "
#                 f"{format_time(st.session_state.playback_state['total_duration'])}"
#             )
        
#         # Playback controls
#         col1, col2, col3 = st.columns([1, 1, 1])
        
#         with col1:
#             if st.button("⏮️ Previous", use_container_width=True):
#                 play_previous_chapter(book['id'], chapter['chapter_number'])
        
#         with col2:
#             play_pause_text = "⏸️ Pause" if st.session_state.playback_state['is_playing'] else "▶️ Play"
#             if st.button(play_pause_text, use_container_width=True, key="play_pause"):
#                 st.session_state.playback_state['is_playing'] = not st.session_state.playback_state['is_playing']
#                 st.session_state.playback_state['last_update'] = time.time() if st.session_state.playback_state['is_playing'] else None
#                 st.rerun()
        
#         with col3:
#             if st.button("⏭️ Next", use_container_width=True):
#                 play_next_chapter(book['id'], chapter['chapter_number'])
        
#         # Simulate playback progress
#         if st.session_state.playback_state['is_playing']:
#             if st.session_state.playback_state['last_update'] is None:
#                 st.session_state.playback_state['last_update'] = time.time()
            
#             elapsed = time.time() - st.session_state.playback_state['last_update']
#             st.session_state.playback_state['current_time'] += elapsed
#             st.session_state.playback_state['last_update'] = time.time()
            
#             # Update progress percentage
#             if st.session_state.playback_state['total_duration'] > 0:
#                 st.session_state.playback_state['progress_percent'] = (
#                     st.session_state.playback_state['current_time'] / 
#                     st.session_state.playback_state['total_duration'] * 100
#                 )
            
#             # Auto-rerun to update UI
#             time.sleep(0.1)
#             st.rerun()
        
#         # Periodically update progress in database (every 5 seconds)
#         current_time = time.time()
#         if (st.session_state.playback_state['last_progress_update'] is None or 
#             current_time - st.session_state.playback_state['last_progress_update'] > 5):
#             update_playback_progress()
#             st.session_state.playback_state['last_progress_update'] = current_time
        
#         # Download button
#         try:
#             # Download the audio file
#             audio_response = requests.get(audio_url, timeout=30)
#             if audio_response.status_code == 200:
#                 st.download_button(
#                     label="📥 Download MP3",
#                     data=audio_response.content,
#                     file_name=f"{sanitize_filename(book['title'])}_Chapter_{chapter['chapter_number']}.mp3",
#                     mime="audio/mp3",
#                     use_container_width=True
#                 )
                
#                 # Record download in database
#                 api_record_download(
#                     user_id=st.session_state.user_id,
#                     book_id=book['id'],
#                     chapter_id=chapter['id'],
#                     file_path=audio_url,
#                     file_size=len(audio_response.content)
#                 )
#             else:
#                 st.warning("Download temporarily unavailable")
#         except Exception as e:
#             st.warning(f"Download error: {str(e)}")
        
#         # Book information
#         st.markdown("---")
#         col_info1, col_info2 = st.columns(2)
        
#         with col_info1:
#             st.write(f"**Book:** {book['title']}")
#             st.write(f"**Author:** {book.get('author', 'Unknown')}")
#             st.write(f"**Chapter:** {chapter['chapter_number']}. {chapter['title']}")
        
#         with col_info2:
#             if book.get('category_name'):
#                 st.write(f"**Category:** {book['category_name']}")
#             st.write(f"**Progress:** {st.session_state.playback_state['progress_percent']:.1f}%")
#             if st.session_state.playback_state['is_playing']:
#                 st.write("**Status:** Playing")
#             else:
#                 st.write("**Status:** Paused")
                
def update_playback_progress():
    """Update playback progress in database - ENHANCED DEBUGGING"""
    print("🔄 update_playback_progress() called")
    
    # Debug: Check what's in session state
    print("📊 Session state keys:", list(st.session_state.keys()))
    
    if 'currently_playing' not in st.session_state:
        print("❌ currently_playing NOT found in session state")
        return False
        
    playback = st.session_state.currently_playing
    print(f"📊 Currently playing: {playback}")
    
    if 'user_info' not in st.session_state:
        print("❌ user_info NOT found in session state")
        return False
    
    user_id = st.session_state.user_info.get('id')
    print(f"👤 User ID: {user_id}")
    
    if 'playback_state' not in st.session_state:
        print("❌ playback_state NOT found in session state")
        return False
    
    playback_state = st.session_state.playback_state
    print(f"⏱️ Playback state to save: {playback_state}")
    
    # Get current progress from playback state
    current_time = playback_state.get('current_time', 0)
    progress_percent = playback_state.get('progress_percent', 0)
    
    print(f"📈 Sending to API - Duration: {current_time}s, Progress: {progress_percent}%")
    
    # Update via API
    success = update_playback_progress_streamlit(
        user_id=user_id,
        book_id=playback['book_id'],
        chapter_id=playback['chapter_id'],
        duration=current_time,
        progress=progress_percent
    )
    
    print(f"✅ API call result: {success}")
    return success

# def display_audio_player(book, chapter, audio_url):
#     """Display the audio player with controls"""
#     st.success(f"🎵 Now Playing: {book['title']} - Chapter {chapter['chapter_number']}")
    
#     # Create a container for the audio player
#     player_container = st.container()
    
#     with player_container:
#         # Audio player
#         st.audio(audio_url, format="audio/mp3")
        
#         # Playback controls
#         col1, col2, col3 = st.columns([1, 1, 1])
        
#         with col1:
#             if st.button("⏮️ Previous Chapter", use_container_width=True):
#                 play_previous_chapter(book['id'], chapter['chapter_number'])
        
#         with col2:
#             if st.button("⏯️ Pause/Play", use_container_width=True):
#                 # You can implement pause/play functionality here
#                 st.rerun()
        
#         with col3:
#             if st.button("⏭️ Next Chapter", use_container_width=True):
#                 play_next_chapter(book['id'], chapter['chapter_number'])
        
#         # Download button
#         try:
#             # Download the audio file
#             audio_response = requests.get(audio_url, timeout=30)
#             if audio_response.status_code == 200:
#                 st.download_button(
#                     label="📥 Download MP3",
#                     data=audio_response.content,
#                     file_name=f"{sanitize_filename(book['title'])}_Chapter_{chapter['chapter_number']}.mp3",
#                     mime="audio/mp3",
#                     use_container_width=True
#                 )
                
#                 # Record download in database
#                 api_record_download(
#                     user_id=st.session_state.user_id,
#                     book_id=book['id'],
#                     chapter_id=chapter['id'],
#                     file_path=audio_url,
#                     file_size=len(audio_response.content)
#                 )
#             else:
#                 st.warning("Download temporarily unavailable")
#         except Exception as e:
#             st.warning(f"Download error: {str(e)}")
        
#         # Book information
#         st.markdown("---")
#         st.write(f"**Book:** {book['title']}")
#         st.write(f"**Author:** {book.get('author', 'Unknown')}")
#         st.write(f"**Chapter:** {chapter['chapter_number']}. {chapter['title']}")
        
#         if book.get('category_name'):
#             st.write(f"**Category:** {book['category_name']}")


######## my_library - show_recently_played - play_previous_chapter ########
def play_previous_chapter(book_id, current_chapter_number):
    """Play the previous chapter"""
    # Finalize current playback
    finalize_playback()
    
    previous_chapter = get_chapter_by_number(book_id, current_chapter_number - 1)
    if previous_chapter:
        play_book(book_id, chapter_id=previous_chapter['id'])
    else:
        st.warning("No previous chapter available")

######## my_library - show_recently_played - play_next_chapter ########
def play_next_chapter(book_id, current_chapter_number):
    """Play the next chapter"""
    # Finalize current playback
    finalize_playback()
    
    next_chapter = get_chapter_by_number(book_id, current_chapter_number + 1)
    if next_chapter:
        play_book(book_id, chapter_id=next_chapter['id'])
    else:
        st.warning("No next chapter available")

######## my_library - show_recently_played - finalize_playback ########
def finalize_playback():
    """Finalize playback by updating final progress"""
    if 'currently_playing' in st.session_state:
        # Update progress one last time
        update_playback_progress()
        
        # Clear playback state
        if 'playback_state' in st.session_state:
            st.session_state.playback_state = {
                'is_playing': False,
                'current_time': 0,
                'total_duration': 300,
                'progress_percent': 0
            }

######## my_library - sanitize_filename ########
######## browse_books - sanitize_filename ########
def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    import re
    return re.sub(r'[<>:"/\\|?*]', '', filename)

######## my_library - show_recently_played - record_download ########
def api_record_download(user_id, book_id, chapter_id=None, file_path="", file_size=0):
    """Streamlit function to record download via API"""
    try:
        payload = {
            "user_id": user_id,
            "book_id": book_id,
            "chapter_id": chapter_id,
            "file_path": file_path,
            "file_size": file_size
        }
        
        response = requests.post(
            f"{API_URL}/api/record-download",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                st.success("Download recorded successfully!")
                return True
            else:
                st.error(f"Failed to record download: {data.get('error', 'Unknown error')}")
                return False
        else:
            st.error(f"Failed to record download: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return False
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return False
######## END - my_library ########

###########################################################################################################
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
    
# def update_playback_progress_streamlit(user_id, book_id, chapter_id=None, duration=0, progress=0):
#     """Update playback progress via API"""
#     print("update_playback_progress_streamlit")
#     try:
#         progress_int = int(round(progress))
#         duration_int = int(round(duration))
        
#         print(f"🔄 Converting progress: {progress} → {progress_int} (int)")
#         print(f"🔄 Converting duration: {duration} → {duration_int} (int)")

#         payload = {
#             "user_id": user_id,
#             "book_id": book_id,
#             "chapter_id": chapter_id,
#             "duration": duration,
#             "progress": progress
#         }
        
#         response = requests.post(
#             f"{API_URL}/api/update-playback",
#             json=payload,
#             timeout=5
#         )
        
#         if response.status_code == 200:
#             data = response.json()
#             return data.get('success', False)
#         else:
#             print(f"Failed to update progress: {response.status_code}")
#             return False
            
#     except Exception as e:
#         print(f"❌ Error updating playback progress: {str(e)}")
#         return False
    

def record_audio_play_streamlit(user_id, book_id, chapter_id=None, duration=0, progress=0):
    """Record initial play via API"""
    try:
        progress_int = int(round(progress))
        duration_int = int(round(duration))
        payload = {
            "user_id": user_id,
            "book_id": book_id,
            "chapter_id": chapter_id,
            "duration": duration_int,
            "progress": progress_int
        }
        
        response = requests.post(
            f"{API_URL}/api/record-play",
            json=payload,
            timeout=5
        )
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error recording audio play: {str(e)}")
        return False



def show_favorites():
    """Show user's favorite books"""
    # Your favorites logic here
    pass

def show_downloads():
    """Show user's downloads"""
    # Your downloads logic here
    pass

def show_reading_history():
    """Show reading history"""
    # Your history logic here
    pass


def display_progress_info(book):
    """Display progress information for a book"""
    progress = book.get('progress', 0)
    duration = book.get('duration', 0)
    total_chapters = book.get('total_chapters', 0)
    current_chapter = book.get('chapter_number', 0)
    
    # Display progress bar
    if progress > 0:
        st.progress(progress / 100)
    
    # Show detailed progress information
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Overall Progress:** {progress}%")
        if duration > 0:
            # Convert seconds to minutes:seconds
            minutes = duration // 60
            seconds = duration % 60
            st.write(f"**Time listened:** {minutes}:{seconds:02d}")
    
    with col2:
        if total_chapters > 0 and current_chapter > 0:
            st.write(f"**Chapter:** {current_chapter}/{total_chapters}")
            chapter_progress = (current_chapter / total_chapters) * 100
            st.write(f"**Chapter Progress:** {chapter_progress:.1f}%")



# import time
# from datetime import datetime, timedelta

def display_audio_player_simple(book, chapter, audio_url):
    """Simple audio player with time-based progress simulation"""
    
    def auto_save_progress():
        """Automatically save progress when significant changes occur"""
        print(f"💾 Auto-saving: {playback_state['current_time']}s, {playback_state['progress_percent']}%")
        if update_playback_progress():
            print("✅ Progress auto-saved")
            playback_state['last_saved_time'] = playback_state['current_time']
        else:
            print("❌ Failed to auto-save progress")
    
    st.success(f"🎵 Now Playing: {book['title']}" + 
              (f" - Chapter {chapter['chapter_number']}" if chapter else ""))
    
    # Standard audio player
    st.audio(audio_url, format="audio/mp3")
    
    # Ensure playback_state exists
    if 'playback_state' not in st.session_state:
        st.session_state.playback_state = {
            'is_playing': False,
            'current_time': 0,
            'total_duration': 300,
            'progress_percent': 0,
            'last_update': datetime.now(),
            'last_progress_update': None,
            'last_saved_time': 0
        }
    
    playback_state = st.session_state.playback_state
    
    # Initialize tracking variables if they don't exist
    if 'playback_last_update' not in st.session_state:
        st.session_state.playback_last_update = datetime.now()
    
    # Calculate current time based on playback state
    current_time = playback_state.get('current_time', 0)
    
    # If playing, increment time automatically
    if playback_state.get('is_playing', False):
        time_since_last_update = (datetime.now() - st.session_state.playback_last_update).total_seconds()
        current_time += time_since_last_update
        st.session_state.playback_last_update = datetime.now()
        print(f"⏱️ Time update: +{time_since_last_update:.1f}s = {current_time:.1f}s")
    
    # Ensure time doesn't exceed total duration
    total_duration = playback_state.get('total_duration', 300)
    current_time = min(current_time, total_duration)
    
    # Update playback state
    playback_state['current_time'] = current_time
    playback_state['progress_percent'] = (current_time / total_duration) * 100 if total_duration > 0 else 0
    
    # Progress slider
    new_time = st.slider(
        "Progress",
        min_value=0,
        max_value=total_duration,
        value=int(current_time),
        format="%d seconds",
        key="progress_slider_simple"
    )
    
    # Update if slider changed
    if new_time != current_time:
        playback_state['current_time'] = new_time
        playback_state['progress_percent'] = (new_time / total_duration) * 100 if total_duration > 0 else 0
        st.session_state.playback_last_update = datetime.now()
        print(f"🎚️ Slider changed to: {new_time}s")
        auto_save_progress()
    
    # Display time and progress
    col_time, col_progress = st.columns(2)
    with col_time:
        st.write(f"**Time:** {format_time(playback_state['current_time'])} / {format_time(total_duration)}")
    with col_progress:
        progress_percent = playback_state.get('progress_percent', 0)
        st.write(f"**Progress:** {progress_percent:.1f}%")
        if progress_percent > 0:
            st.progress(progress_percent / 100)
    
    # Playback controls
    if chapter:
        st.write("**Playback Controls:**")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("⏮️ Previous", key="prev_simple", use_container_width=True):
                update_playback_progress()
                play_previous_chapter_safe(book['id'], chapter['chapter_number'])
        
        with col2:
            play_text = "⏸️ Pause" if playback_state.get('is_playing', False) else "▶️ Play"
            if st.button(play_text, key="play_pause_simple", use_container_width=True):
                was_playing = playback_state.get('is_playing', False)
                playback_state['is_playing'] = not was_playing
                st.session_state.playback_last_update = datetime.now()
                
                print(f"⏯️ Play/Pause: {was_playing} -> {playback_state['is_playing']}")
                
                # Auto-save when pausing
                if was_playing:  # If we were playing and now pausing
                    auto_save_progress()
                
                st.rerun()
        
        with col3:
            if st.button("⏭️ Next", key="next_simple", use_container_width=True):
                update_playback_progress()
                play_next_chapter_safe(book['id'], chapter['chapter_number'])
    
    # Auto-save logic - FIXED
    if playback_state.get('is_playing', False):
        current_time = playback_state.get('current_time', 0)
        last_saved_time = playback_state.get('last_saved_time', 0)
        last_save = playback_state.get('last_progress_update')
        
        # Auto-save every 10 seconds or if significant progress made
        should_auto_save = False
        
        if last_save is None:
            should_auto_save = True
        else:
            time_since_last_save = (datetime.now() - last_save).total_seconds()
            progress_since_last_save = abs(current_time - last_saved_time)
            
            if time_since_last_save >= 10 or progress_since_last_save >= 5:
                should_auto_save = True
                print(f"🕒 Auto-save check: {time_since_last_save:.1f}s since last save, {progress_since_last_save:.1f}s progress")
        
        if should_auto_save:
            auto_save_progress()
            playback_state['last_progress_update'] = datetime.now()
    
    # Manual save button
    if st.button("💾 Save Progress Now", key="save_simple", use_container_width=True):
        print("💾 Manual save requested")
        if update_playback_progress():
            st.success("✅ Progress saved!")
            st.rerun()
        else:
            st.error("❌ Failed to save progress")
    
    # Debug info
    if DEBUG:
        with st.expander("🔧 Debug Info"):
            st.write("**Playback State:**")
            st.json(playback_state)
            st.write(f"**Last Update:** {st.session_state.playback_last_update}")