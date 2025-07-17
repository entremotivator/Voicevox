import streamlit as st
import streamlit.components.v1 as components
import base64
import requests
import json
import time

# Page configuration
st.set_page_config(
    page_title="🎙️ Smart Voice Chat", 
    layout="centered",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'is_recording' not in st.session_state:
    st.session_state.is_recording = False
if 'auto_send_audio' not in st.session_state:
    st.session_state.auto_send_audio = None
if 'api_response' not in st.session_state:
    st.session_state.api_response = None

# Sidebar for API key and settings
st.sidebar.title("🔐 Configuration")
api_key = st.sidebar.text_input("Mistral API Key", type="password", key="api_key")
st.sidebar.markdown("---")
st.sidebar.markdown("### 🎛️ Settings")
model_name = st.sidebar.selectbox("Model", ["voxtral-mini-2507"], index=0)
auto_play = st.sidebar.checkbox("Auto-play responses", value=True)
show_transcript = st.sidebar.checkbox("Show text transcript", value=True)
auto_send = st.sidebar.checkbox("Auto-send after recording", value=True)
show_json = st.sidebar.checkbox("Show JSON response", value=False)

# Main interface
st.title("🗣️ Smart Voice Chat")
st.markdown("Talk naturally with Mistral AI - just like a conversation!")

# Display conversation history
if st.session_state.messages:
    st.markdown("### 💬 Conversation")
    for i, msg in enumerate(st.session_state.messages):
        if msg['role'] == 'user':
            with st.chat_message("user", avatar="🧑"):
                if 'audio' in msg:
                    st.audio(msg['audio'])
                if 'text' in msg and show_transcript:
                    st.write(f"*{msg['text']}*")
        else:
            with st.chat_message("assistant", avatar="🤖"):
                if 'text' in msg:
                    st.write(msg['text'])
                if 'audio' in msg:
                    st.audio(msg['audio'], autoplay=auto_play)

# Show JSON response if enabled
if show_json and st.session_state.api_response:
    st.markdown("### 📄 Latest API Response")
    with st.expander("Show JSON Response", expanded=False):
        st.json(st.session_state.api_response)

# Clear conversation button
if st.session_state.messages:
    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.experimental_rerun()

st.markdown("---")

# Enhanced voice recorder with better UX
st.markdown("### 🎤 Voice Input")

# JavaScript-based recorder with improved functionality
recorder_html = """
<div id="voice-recorder" style="text-align: center; padding: 20px;">
    <button id="recordButton" style="
        background: linear-gradient(45deg, #ff6b6b, #ff8e8e);
        color: white;
        border: none;
        padding: 15px 30px;
        font-size: 16px;
        border-radius: 25px;
        cursor: pointer;
        margin: 10px;
        transition: all 0.3s ease;
    ">🎙️ Start Recording</button>
    
    <button id="stopButton" disabled style="
        background: linear-gradient(45deg, #666, #888);
        color: white;
        border: none;
        padding: 15px 30px;
        font-size: 16px;
        border-radius: 25px;
        cursor: pointer;
        margin: 10px;
        transition: all 0.3s ease;
    ">⏹️ Stop Recording</button>
    
    <div id="status" style="
        margin: 20px 0;
        font-size: 18px;
        font-weight: bold;
        color: #333;
    ">Ready to record</div>
    
    <div id="waveform" style="
        width: 100%;
        height: 60px;
        background: #f0f0f0;
        border-radius: 10px;
        margin: 20px 0;
        display: none;
        position: relative;
        overflow: hidden;
    "></div>
    
    <audio id="audioPlayback" controls style="
        width: 100%;
        margin: 20px 0;
        display: none;
    "></audio>
    
    <textarea id="base64output" style="display: none;"></textarea>
</div>

<script>
let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let recordingTimer;
let seconds = 0;

const recordBtn = document.getElementById("recordButton");
const stopBtn = document.getElementById("stopButton");
const statusText = document.getElementById("status");
const playback = document.getElementById("audioPlayback");
const base64output = document.getElementById("base64output");
const waveform = document.getElementById("waveform");

// Update button styles
function updateButtonStyles() {
    if (isRecording) {
        recordBtn.style.background = "linear-gradient(45deg, #666, #888)";
        recordBtn.style.cursor = "not-allowed";
        stopBtn.style.background = "linear-gradient(45deg, #ff4757, #ff6b6b)";
        stopBtn.style.cursor = "pointer";
    } else {
        recordBtn.style.background = "linear-gradient(45deg, #ff6b6b, #ff8e8e)";
        recordBtn.style.cursor = "pointer";
        stopBtn.style.background = "linear-gradient(45deg, #666, #888)";
        stopBtn.style.cursor = "not-allowed";
    }
}

// Timer function
function startTimer() {
    seconds = 0;
    recordingTimer = setInterval(() => {
        seconds++;
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        statusText.innerHTML = `🔴 Recording... ${mins}:${secs.toString().padStart(2, '0')}`;
    }, 1000);
}

function stopTimer() {
    clearInterval(recordingTimer);
}

// Visual feedback for recording
function showRecordingFeedback() {
    waveform.style.display = 'block';
    waveform.innerHTML = '<div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #666;">🎵 Recording audio waves...</div>';
}

recordBtn.onclick = async () => {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                sampleRate: 44100
            }
        });
        
        mediaRecorder = new MediaRecorder(stream, {
            mimeType: 'audio/webm'
        });
        
        audioChunks = [];
        isRecording = true;
        
        mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
        mediaRecorder.onstop = async () => {
            const blob = new Blob(audioChunks, { type: 'audio/webm' });
            const arrayBuffer = await blob.arrayBuffer();
            const base64String = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));
            base64output.value = base64String;
            playback.src = URL.createObjectURL(blob);
            playback.style.display = 'block';
            statusText.innerHTML = "✅ Recording complete! Processing...";
            waveform.style.display = 'none';
            
            // Auto-send if enabled
            if (window.parent && window.parent.postMessage) {
                window.parent.postMessage({
                    type: 'AUDIO_RECORDED',
                    data: base64String
                }, '*');
            }
            
            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        startTimer();
        showRecordingFeedback();
        recordBtn.disabled = true;
        stopBtn.disabled = false;
        updateButtonStyles();
        
    } catch (err) {
        statusText.innerHTML = "❌ Error: " + err.message;
        console.error('Error accessing microphone:', err);
    }
};

stopBtn.onclick = () => {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        stopTimer();
        isRecording = false;
        recordBtn.disabled = false;
        stopBtn.disabled = true;
        updateButtonStyles();
    }
};

// Initialize button styles
updateButtonStyles();
</script>
"""

# Display the recorder
recorder_component = components.html(recorder_html, height=350)

# Auto-send functionality
if auto_send and api_key:
    # Use a callback to detect when recording is complete
    audio_data_placeholder = st.empty()
    
    # JavaScript to communicate with parent
    components.html("""
    <script>
    window.addEventListener('message', function(event) {
        if (event.data.type === 'AUDIO_RECORDED') {
            // Trigger Streamlit rerun with audio data
            const audioData = event.data.data;
            if (audioData) {
                // Set the audio data in session state
                window.parent.postMessage({
                    type: 'STREAMLIT_SET_AUDIO',
                    data: audioData
                }, '*');
            }
        }
    });
    </script>
    """, height=0)

# Check for auto-send audio
if st.session_state.auto_send_audio and api_key:
    audio_data = st.session_state.auto_send_audio
    st.session_state.auto_send_audio = None  # Clear after use
    
    with st.spinner("🤖 Auto-sending to Mistral..."):
        # Process the audio (same logic as manual send)
        try:
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
                                "data": audio_data.strip(),
                                "format": "webm"
                            }
                        }
                    ]
                }
            ]

            data = {
                "model": model_name,
                "messages": messages
            }

            response = requests.post(
                "https://api.mistral.ai/v1/chat/completions", 
                headers=headers, 
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                st.session_state.api_response = result  # Store full JSON response
                content = result["choices"][0]["message"]["content"]
                
                # Store user message
                user_msg = {"role": "user", "audio": base64.b64decode(audio_data)}
                st.session_state.messages.append(user_msg)
                
                # Process Mistral's response
                assistant_msg = {"role": "assistant"}
                
                for item in content:
                    if item["type"] == "text":
                        assistant_msg["text"] = item["text"]
                    elif item["type"] == "output_audio":
                        assistant_msg["audio"] = base64.b64decode(item["audio"]["data"])
                
                st.session_state.messages.append(assistant_msg)
                st.success("✅ Auto-sent and response received!")
                st.experimental_rerun()
                
            else:
                st.error(f"❌ API Error: {response.status_code}")
                st.code(response.text)
                
        except Exception as e:
            st.error(f"💥 Auto-send error: {str(e)}")

# Get the base64 audio data
base64_audio = st.text_area("", height=1, key="base64_input", label_visibility="hidden")

# Manual send button (only shown if auto-send is disabled)
if not auto_send:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        send_button = st.button("🚀 Send to Mistral", disabled=not api_key)
    
    with col2:
        if st.button("🎤 Quick Record & Send", disabled=not api_key):
            st.info("Use the recorder above, then click 'Send to Mistral'")
else:
    st.info("🔄 Auto-send is enabled - your recordings will be sent automatically!")
    send_button = False

# Process the audio when send button is clicked (manual mode)
if send_button and api_key:
    # Get base64 from the hidden textarea (populated by JavaScript)
    base64_from_js = st.text_input("", key="js_base64", label_visibility="hidden")
    
    if base64_from_js or base64_audio:
        audio_data = base64_from_js or base64_audio
        
        with st.spinner("🤖 Mistral is thinking..."):
            try:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }

                # Prepare the message
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_audio",
                                "input_audio": {
                                    "data": audio_data.strip(),
                                    "format": "webm"
                                }
                            }
                        ]
                    }
                ]

                data = {
                    "model": model_name,
                    "messages": messages
                }

                # Send request to Mistral
                response = requests.post(
                    "https://api.mistral.ai/v1/chat/completions", 
                    headers=headers, 
                    json=data,
                    timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    st.session_state.api_response = result  # Store full JSON response
                    content = result["choices"][0]["message"]["content"]
                    
                    # Store user message
                    user_msg = {"role": "user", "audio": base64.b64decode(audio_data)}
                    st.session_state.messages.append(user_msg)
                    
                    # Process Mistral's response
                    assistant_msg = {"role": "assistant"}
                    
                    for item in content:
                        if item["type"] == "text":
                            assistant_msg["text"] = item["text"]
                        elif item["type"] == "output_audio":
                            assistant_msg["audio"] = base64.b64decode(item["audio"]["data"])
                    
                    st.session_state.messages.append(assistant_msg)
                    
                    # Success message
                    st.success("✅ Response received!")
                    st.experimental_rerun()
                    
                else:
                    st.error(f"❌ API Error: {response.status_code}")
                    st.code(response.text)
                    
            except requests.exceptions.Timeout:
                st.error("⏱️ Request timed out. Please try again.")
            except requests.exceptions.RequestException as e:
                st.error(f"🌐 Network error: {str(e)}")
            except Exception as e:
                st.error(f"💥 Unexpected error: {str(e)}")
    else:
        st.warning("🎙️ Please record some audio first!")

# Instructions
st.markdown("---")
st.markdown("### 📋 How to use:")
st.markdown("""
1. **Enter your Mistral API key** in the sidebar
2. **Enable/disable auto-send** in sidebar settings
3. **Click 'Start Recording'** and speak clearly
4. **Click 'Stop Recording'** when finished
5. **Audio will auto-send** (if enabled) or use manual send button
6. **View JSON responses** by enabling the option in sidebar
7. **Continue the conversation** naturally!
""")

st.markdown("### ⚙️ Features:")
st.markdown("""
- 🔄 **Auto-send after recording** - No need to click send!
- 📊 **JSON response viewer** - See the full API response
- 🎵 **Auto-play responses** - Hear Mistral's voice automatically
- 📝 **Text transcripts** - Read what was said
- 💬 **Conversation history** - Keep track of your chat
- 🎛️ **Customizable settings** - Adjust to your preferences
""")

# Footer
st.markdown("---")
st.markdown("*Built with Streamlit and Mistral AI* 🚀")
