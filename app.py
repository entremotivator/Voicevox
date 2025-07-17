import streamlit as st
import requests
import base64
import os
import tempfile

st.set_page_config(page_title="🎙️ Chat with Mistral Voxtral", layout="centered")

# Sidebar API Key
st.sidebar.title("🔐 Mistral API Key")
api_key = st.sidebar.text_input("Enter your MISTRAL API Key", type="password")

st.title("🗣️ Talk to Mistral with Your Voice")
st.write("Record your voice, ask a question, and get a spoken reply!")

# Record audio (Streamlit's recorder returns .wav)
audio_data = st.audio_recorder("🎤 Record your voice", key="rec", format="audio/wav")

# Optional: Text prompt if you want to include extra context
user_question = st.text_input("💬 (Optional) Add a question for Mistral", placeholder="e.g. What did I just say?")

if st.button("🚀 Send to Mistral") and audio_data and api_key:
    with st.spinner("Transmitting voice to Mistral..."):

        # Save to temp .wav
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_data)
            tmp_path = tmp_file.name

        # Read and base64 encode the wav audio
        with open(tmp_path, "rb") as f:
            encoded_audio = base64.b64encode(f.read()).decode("utf-8")

        # Prepare API request
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "voxtral-mini-2507",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": encoded_audio,
                                "format": "wav"
                            }
                        }
                    ]
                }
            ]
        }

        # Include optional text
        if user_question:
            data["messages"][0]["content"].append({
                "type": "text",
                "text": user_question
            })

        # Send request to Mistral
        response = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json=data)

        if response.status_code == 200:
            message = response.json()["choices"][0]["message"]["content"]

            for item in message:
                if item["type"] == "text":
                    st.success("🧠 Mistral replied:")
                    st.write(item["text"])
                elif item["type"] == "output_audio":
                    st.audio(base64.b64decode(item["audio"]["data"]), format="audio/mp3")
        else:
            st.error(f"❌ Error {response.status_code}")
            st.write(response.text)

        os.remove(tmp_path)
else:
    st.info("🎙️ Please record audio and enter your API key.")
