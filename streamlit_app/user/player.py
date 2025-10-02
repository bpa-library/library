# streamlit_app/user/player.py
import streamlit as st
from streamlit.components.v1 import html
import requests
import os
# from streamlit_app.config import API_URL
# from .library import my_library

from dotenv import load_dotenv
load_dotenv()
API_URL = os.getenv('API_URL', 'http://localhost:8000')
# API_URL = os.environ.get("API_URL", "http://localhost:5000")

def show_audio_player(user_id, book_id, chapter_id, audio_url):
    """Streamlit component: HTML5 audio player with progress sync"""

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


# import streamlit as st
# from user.player import show_audio_player



if __name__ == "__main__":
    st.title("📚 Listen to Book")
    # file = "file:///E:/Books-Audible/BPA/Bharat na 75 filmudhyog na shreshth kasabio By Nirali badiyani/aud002.mp3"
    # file = "E:\\Books-Audible\\BPA\\Bharat na 75 filmudhyog na shreshth kasabio By Nirali badiyani\\aud002.mp3"
    user_id = st.session_state.get("user_id", 4)  # replace with real login session
    book_id = 603
    chapter_id = 3
    # audio_url = "http://localhost:5000/static/audio/myaudio.ogg"
    audio_url = "http://127.0.0.1:8000/audio/aud002.mp3"
    # audio_url = file

    show_audio_player(user_id, book_id, chapter_id, audio_url)