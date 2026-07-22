import streamlit as st
import json
import os
from groq import Groq

# 1. SET YOUR FREE GROQ API KEY HERE
API_KEY = st.secrets["GROQ_API_KEY"]

client = Groq(api_key=API_KEY)
SAVE_FILE = "language_save.json"

st.set_page_config(page_title="AI Language Companion", layout="centered")
st.title("🗣️ AI Language Learning Companion")
st.subheader("Practice speaking like a native with your personal AI friend!")

# --- INITIALIZE SESSION DATA ---
if "messages" not in st.session_state:
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as file:
            saved_data = json.load(file)
            st.session_state.messages = saved_data.get("messages", [])
            st.session_state.language = saved_data.get("language", "")
            st.session_state.topic = saved_data.get("topic", "")
    else:
        st.session_state.messages = []
        st.session_state.language = ""
        st.session_state.topic = ""

def save_language_state():
    state_data = {
        "messages": st.session_state.messages,
        "language": st.session_state.language,
        "topic": st.session_state.topic
    }
    with open(SAVE_FILE, "w") as file:
        json.dump(state_data, file)

# --- MAIN MENU: LANGUAGE & TOPIC SELECTION ---
if not st.session_state.messages:
    st.subheader("Configure Your Practice Session:")
    
    selected_lang = st.selectbox(
        "Which language do you want to practice?",
        ["Japanese 🇯🇵", "Spanish 🇪🇸", "Korean 🇰🇷", "English 🇺🇸", "French 🇫🇷"]
    )
    
    selected_topic = st.text_input(
        "Enter a conversation topic or scenario:",
        placeholder="e.g., Ordering food at a cafe, Chatting about hobbies..."
    )
    
    if st.button("🚀 Start Chatting!") and selected_topic:
        st.session_state.language = selected_lang
        st.session_state.topic = selected_topic
        
        # Rigid, structured constraints forcing the AI to output localized parameters
        st.session_state.messages = [{
            "role": "system", 
            "content": (
                f"You are a friendly native speaker teaching the user {selected_lang}. "
                f"The setting for the conversation is: '{selected_topic}'. "
                f"You MUST write your primary conversational reply strictly in the target language ({selected_lang}). "
                "Do not introduce your conversation with English words. "
                "Every single response you output MUST follow this exact, structural layout format with strict line breaks:\n\n"
                "[CHAT]: (Write your friendly reply here exclusively in the target language characters/scripts)\n"
                "[CORRECTION]: (If the user made a grammar, vocabulary, or spelling mistake in their previous response, explain it here gently in simple English. If their text was perfect, write 'None')\n"
                "[ROMALESS]: (Write the Romaji or phonetic pronunciation guide for your target language reply here)\n"
                "[ENGLISH]: (Write the clean English translation of your target language reply here)"
            )
        }]
        save_language_state()
        st.rerun()

# --- ACTIVE CONVERSATION INTERFACE ---
else:
    with st.sidebar:
        st.header("📋 Session Profile")
        st.metric(label="🌐 Target Language", value=st.session_state.language)
        st.write(f"💬 **Current Topic:** {st.session_state.topic}")
        
        st.markdown("---")
        if st.button("💥 Change Language / Reset Chat"):
            if os.path.exists(SAVE_FILE):
                os.remove(SAVE_FILE)
            st.session_state.clear()
            st.rerun()

    st.markdown("### 📜 The Conversation Log")
    chat_container = st.container(height=380)
    
    voice_codes = {"Japanese 🇯🇵": "ja-JP", "Spanish 🇪🇸": "es-ES", "Korean 🇰🇷": "ko-KR", "English 🇺🇸": "en-US", "French 🇫🇷": "fr-FR"}
    browser_voice_lang = voice_codes.get(st.session_state.language, "en-US")

    with chat_container:
        total_m = len(st.session_state.messages)
        for idx, msg in enumerate(st.session_state.messages):
            if msg["role"] == "assistant":
                raw_text = str(msg["content"])
                
                # ⚙️ STRING SLICING DECONSTRUCTION MATRIX
                chat_main = ""
                correction_main = ""
                romaji_main = ""
                english_main = ""
                
                # Parse the rigid structure boundaries safely
                if "[CHAT]:" in raw_text and "[CORRECTION]:" in raw_text:
                    try:
                        chat_main = raw_text.split("[CHAT]:")[1].split("[CORRECTION]:")[0].strip()
                        correction_main = raw_text.split("[CORRECTION]:")[1].split("[ROMALESS]:")[0].strip()
                        romaji_main = raw_text.split("[ROMALESS]:")[1].split("[ENGLISH]:")[0].strip()
                        english_main = raw_text.split("[ENGLISH]:")[1].strip()
                    except Exception:
                        chat_main = raw_text # Fallback structure if parsing breaks
                else:
                    chat_main = raw_text

                # Render the clean native script chat bubble (e.g. Pure Japanese Kanji/Kana)
                st.chat_message("assistant", avatar="👩‍🏫").write(chat_main)
                
                # Render the Grammar Lesson warning block only if errors were caught
                if correction_main and correction_main.lower() != "none":
                    st.warning(f"📝 **Grammar Lesson:** {correction_main}")
                
                # 👁️ THE 'SHOW' INTERACTIVE TRANSLATION DROP-DOWN
                if english_main or romaji_main:
                    with st.expander("👁️ Show English Translation & Romaji"):
                        if romaji_main:
                            st.markdown(f"🗣️ **Pronunciation / Romaji:** *{romaji_main}*")
                        if english_main:
                            st.markdown(f"🇺🇸 **English Meaning:** {english_main}")
                
                # 🎙️ ACCENT-SPECIFIC VOICE ENGINE
                if idx == total_m - 1 and chat_main:
                    safe_narr = chat_main.replace('"', '\\"').replace("'", "\\'").replace('\n', ' ')
                    st.components.v1.html(
                        f"""
                        <script>
                        window.parent.speechSynthesis.cancel(); 
                        var msg = new SpeechSynthesisUtterance("{safe_narr}"); 
                        msg.lang = "{browser_voice_lang}"; 
                        msg.rate = 0.85; 
                        window.parent.speechSynthesis.speak(msg);
                        </script>
                        """,
                        height=0
                    )
            elif msg["role"] == "user":
                st.chat_message("user", avatar="👤").write(msg["content"])

    # 2. INTERACTIVE INPUT CONTROLLER
    def clear_text_input():
        if st.session_state.text_move_box:
            st.session_state.messages.append({"role": "user", "content": st.session_state.text_move_box})
            save_language_state()
        st.session_state.text_move_box = ""

    st.text_input(
        "Type your response here...", 
        placeholder="Type in your target language and hit Enter...", 
        key="text_move_box",
        on_change=clear_text_input
    )

    audio_file = st.audio_input("Or click to speak your response...")
    if audio_file is not None:
        with st.spinner("🎙️ Transcribing your voice..."):
            try:
                audio_bytes = audio_file.read()
                transcription = client.audio.transcriptions.create(
                    file=("voice.wav", audio_bytes, "audio/wav"),
                    model="whisper-large-v3",
                    response_format="text"
                )
                spoken_text = str(transcription).strip()
                
                if spoken_text and spoken_text != st.session_state.get("last_voice_input", ""):
                    st.session_state.last_voice_input = spoken_text
                    st.session_state.messages.append({"role": "user", "content": spoken_text})
                    save_language_state()
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Voice Transcription failed: {e}")

    # 3. EXECUTE AI ENGINE
    if st.session_state.messages[-1]["role"] in ["system", "user"]:
        with st.spinner("Your friend is thinking..."):
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            )
            raw_c = res.choices[0].message.content
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": raw_c
            })
            save_language_state()
            st.rerun()
# --- DEVELOPER CREDIT (FIXED FOOTER) ---
st.markdown(
    """
    <style>
    .dev-credit {
        position: fixed;
        bottom: 10px;
        right: 15px;
        background-color: rgba(0, 0, 0, 0.6);
        color: #ffffff;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-family: sans-serif;
        z-index: 999;
        pointer-events: none;
    }
    </style>
    <div class="dev-credit">Created by Kevin DR</div>
    """,
    unsafe_allow_html=True
)
