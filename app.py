import streamlit as st
import streamlit.components.v1 as components
import base64
import requests
import os
import tempfile

st.set_page_config(page_title="🎙️ Mistral Voice Chat", layout="centered")

# API key input
st.sidebar.title("🔐 Mistral API Key")
api_key = st.sidebar.text_input("Enter your MISTRAL API Key", type="password")

st.title("🗣️ Record Your Voice → Mistral Responds with Voice")
st.write("Click 'Start Recording', speak, then click 'Stop'. The app sends your voice to Mistral and gets a voice reply.")

# HTML + JavaScript Recorder UI
st.markdown("### 🎤 Voice Recorder (Browser-based)")
components.html("""
    <html>
    <body>
      <button id="recordButton">🎙️ Start Recording</button>
      <button id="stopButton" disabled>⏹️ Stop</button>
      <p id="status">Not recording</p>
      <audio id="audioPlayback" controls></audio>
      <textarea id="base64output" style="width:100%;height:150px;" placeholder="Base64 will appear here..." readonly></textarea>
      <script>
        let mediaRecorder;
        let audioChunks = [];

        const recordBtn = document.getElementById("recordButton");
        const stopBtn = document.getElementById("stopButton");
        const statusText = document.getElementById("status");
        const playback = document.getElementById("audioPlayback");
        const base64output = document.getElementById("base64output");

        recordBtn.onclick = async () => {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          mediaRecorder = new MediaRecorder(stream);
          audioChunks = [];

          mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
          mediaRecorder.onstop = async () => {
            const blob = new Blob(audioChunks, { type: 'audio/wav' });
            const arrayBuffer = await blob.arrayBuffer();
            const base64String = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));
            base64output.value = base64String;
            playback.src = URL.createObjectURL(blob);
            statusText.innerText = "✅ Recording finished.";
          };

          mediaRecorder.start();
          statusText.innerText = "🔴 Recording...";
          recordBtn.disabled = true;
          stopBtn.disabled = false;
        };

        stopBtn.onclick = () => {
          mediaRecorder.stop();
          recordBtn.disabled = false;
          stopBtn.disabled = true;
        };
      </script>
    </body>
    </html>
""", height=400)

# Manual base64 input
st.markdown("### 🧩 Paste Base64 Audio (From Above)")
base64_audio = st.text_area("Paste base64-encoded WAV audio data from above", height=150)

# Optional text message
user_question = st.text_input("💬 Optional question to Mistral (adds context)", placeholder="e.g. What did I say?")

# Submit button
if st.button("🚀 Send to Mistral") and base64_audio and api_key:
    with st.spinner("Sending to Mistral..."):

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Prepare messages
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": base64_audio.strip(),
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

        # Send request to Mistral
        response = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json=data)

        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]

            for item in content:
                if item["type"] == "text":
                    st.success("🧠 Mistral says:")
                    st.write(item["text"])
                elif item["type"] == "output_audio":
                    st.audio(base64.b64decode(item["audio"]["data"]), format="audio/mp3")
        else:
            st.error(f"❌ API Error: {response.status_code}")
            st.text(response.text)

else:
    st.info("🎙️ Record, paste base64, and enter your API key to start.")

