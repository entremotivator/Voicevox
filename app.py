import streamlit as st
import streamlit.components.v1 as components
import requests
import base64
import tempfile
import os

st.set_page_config(page_title="🎤 Mistral Voice Chat", layout="centered")

# Sidebar: API Key
st.sidebar.title("🔐 Mistral API Key")
api_key = st.sidebar.text_input("Enter your MISTRAL API Key", type="password")

st.title("🗣️ Voice-to-Voice Chat with Mistral")
st.write("Record your voice below, then get a spoken response from Mistral!")

# HTML + JS mic recorder
components.html("""
  <html>
    <body>
      <button id="recordButton">🎙️ Start Recording</button>
      <button id="stopButton" disabled>⏹️ Stop</button>
      <p id="status"></p>
      <audio id="audioPlayback" controls></audio>
      <script>
        let mediaRecorder;
        let audioChunks = [];

        const recordButton = document.getElementById("recordButton");
        const stopButton = document.getElementById("stopButton");
        const status = document.getElementById("status");
        const playback = document.getElementById("audioPlayback");

        recordButton.onclick = async () => {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          mediaRecorder = new MediaRecorder(stream);
          audioChunks = [];

          mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
          mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            const arrayBuffer = await audioBlob.arrayBuffer();
            const base64String = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));
            window.parent.postMessage({ type: "audio", data: base64String }, "*");
            playback.src = URL.createObjectURL(audioBlob);
          };

          mediaRecorder.start();
          status.innerText = "🎙️ Recording...";
          recordButton.disabled = true;
          stopButton.disabled = false;
        };

        stopButton.onclick = () => {
          mediaRecorder.stop();
          status.innerText = "✅ Recording complete.";
          recordButton.disabled = false;
          stopButton.disabled = true;
        };
      </script>
    </body>
  </html>
""", height=300)

# Listen for audio from frontend
from streamlit.runtime.scriptrunner import get_script_run_ctx
from streamlit.web.server.websocket_headers import _get_websocket_headers

if "audio_base64" not in st.session_state:
    st.session_state["audio_base64"] = None

ctx = get_script_run_ctx()
if ctx:
    msg = st.experimental_get_query_params()
    # For Cloud, message passing may not work.
    # You can work around this by using a file uploader for now or deploying outside Streamlit Cloud.

# Manual workaround: paste base64 audio string here (while Streamlit Cloud doesn't support direct message passing)
b64_input = st.text_area("Paste base64 audio from browser here (temp workaround)", height=100)

# Optional text
user_question = st.text_input("💬 Optional follow-up question")

if st.button("🎯 Send to Mistral") and b64_input and api_key:
    with st.spinner("Sending to Mistral..."):

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": b64_input.strip(),
                            "format": "wav"
                        }
                    }
                ]
            }
        ]

        if user_question:
            messages[0]["content"].append({
                "type": "text",
                "text": user_question
            })

        data = {
            "model": "voxtral-mini-2507",
            "messages": messages
        }

        response = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json=data)

        if response.status_code == 200:
            output = response.json()["choices"][0]["message"]["content"]
            for item in output:
                if item["type"] == "text":
                    st.success("🧠 Mistral says:")
                    st.write(item["text"])
                elif item["type"] == "output_audio":
                    st.audio(base64.b64decode(item["audio"]["data"]), format="audio/mp3")
        else:
            st.error(f"❌ {response.status_code}")
            st.write(response.text)
