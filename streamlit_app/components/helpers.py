# streamlit_app/components/helpers.py
#########################
from config import API_URL
import requests
import streamlit as st
from streamlit.components.v1 import html

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
    
import re

def extract_chapter_number(filename: str):
    """
    Return chapter number if filename looks like a valid chapter,
    otherwise return None (so it can be skipped).
    """
    name = filename.lower().strip()

    # Matches aud001.mp3, chapter01.mp3, 001.mp3
    match = re.match(r'^(?:aud|chapter)?0*(\d+)\.(mp3|wav|m4a|ogg)$', name)
    if match:
        return int(match.group(1))
    return None
    

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

def audio_player(user_id, book_id, chapter_id, audio_url):
    """Streamlit component: HTML5 audio player with progress sync"""
    print(f"audio_player : API_URL = {API_URL}")
    # 1. Load last saved progress from backend
    progress = 0
    duration = 0
    try:
        resp = requests.get(
            f"{API_URL}/api/get_recently-played",
            params={"user_id": user_id, "limit": 20}, timeout=10
        )
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            for row in data:
                if row["id"] == book_id and row["chapter_id"] == chapter_id:
                    progress = int(row.get("progress") or 0)
                    duration = int(row.get("duration") or 0)
    except Exception as e:
        st.warning(f"Could not fetch progress: {e}")

    st.write(f"▶️ Restoring from **{progress} sec**")

    # 2. Inject HTML + JS
    html_code = f"""
    <div style="font-family: sans-serif;">
      <audio id="player" controls style="width:100%;">
        <source src="{audio_url}" />
        Your browser does not support the audio element.
      </audio>

      <!-- div style="margin-top:8px;">
        <button id="rew">⏪ 15s</button>
        <button id="fwd">15s ⏩</button>
        <span id="timeinfo">0:00 / 0:00</span>
      </div -->
      
      <div id="status" style="margin-top:6px;color:gray;font-size:13px;">Status: Idle</div>
    </div>

    <script>
    const player = document.getElementById('player');
    const timeinfo = document.getElementById('timeinfo');
    const status = document.getElementById('status');
    const rew = document.getElementById('rew');
    const fwd = document.getElementById('fwd');

    const apiUrl = "{API_URL}/api/update-playback";
    const user_id = {user_id};
    const book_id = {book_id};
    const chapter_id = {chapter_id};
    const initial_progress = {progress};

    function secsToMMSS(s){{s=Math.floor(s);const m=Math.floor(s/60);const ss=s%60;return m+":"+(ss<10?"0"+ss:ss);}}

    player.addEventListener('loadedmetadata', () => {{
      let dur = Math.floor(player.duration || 0);
      let restore = initial_progress;
      if (restore > 0 && restore < dur) {{
        player.currentTime = restore;
      }}
      updateTimeInfo();
    }});

    player.addEventListener('timeupdate', updateTimeInfo);
    player.addEventListener('pause', () => saveProgress(false));
    player.addEventListener('ended', () => saveProgress(true));

    /*
    rew.addEventListener('click', () => {{
      player.currentTime = Math.max(0, player.currentTime - 15);
    }});
    fwd.addEventListener('click', () => {{
      player.currentTime = Math.min(player.duration, player.currentTime + 15);
    }});
    */

    function updateTimeInfo(){{
      const cur = Math.floor(player.currentTime||0);
      const dur = Math.floor(player.duration||0);
      timeinfo.textContent = secsToMMSS(cur)+" / "+secsToMMSS(dur);
    }}

    function saveProgress(final){{
      const dur = Math.floor(player.duration||0);
      const prog = final ? dur : Math.floor(player.currentTime||0);
      const payload = {{
        user_id: user_id,
        book_id: book_id,
        chapter_id: chapter_id,
        duration: dur,
        progress: prog
      }};
      fetch(apiUrl, {{
        method:"POST", headers:{{"Content-Type":"application/json"}},
        body: JSON.stringify(payload), keepalive: true
      }}).then(r => r.json()).then(data => {{
        status.textContent = "Saved at " + prog + "s";
      }}).catch(err => {{
        console.warn("Save error", err);
      }});
    }}

    /* setInterval(() => saveProgress(false), 30000); */

    window.addEventListener('beforeunload', function(e){{
      saveProgress(false);
    }});
    </script>
    """

    html(html_code, height=100)

