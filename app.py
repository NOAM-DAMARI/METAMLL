import streamlit as st
import whisper
import os
import tempfile
import json
import zipfile
import io
from pytube import YouTube
from deep_translator import GoogleTranslator

# הגדרת עיצוב
st.set_page_config(page_title="🎙️ כלי תמלול ותרגום", layout="wide")

st.title("🎙️ כלי תמלול ותרגום אודיו/וידאו")
st.markdown("<hr>", unsafe_allow_html=True)

# העלאת קובץ אודיו/וידאו
uploaded_file = st.file_uploader("📤 העלה קובץ אודיו/וידאו (MP3, MP4)", type=["mp3", "mp4"], key="upload")

# הכנסת קישור ליוטיוב
video_url = st.text_input("🔗 או הדבק קישור ליוטיוב", key="yt_url")

# בחירת שפת תמלול
language = st.selectbox("🌍 בחר שפת תמלול", ["עברית", "אנגלית", "צרפתית", "ספרדית", "גרמנית"], key="lang")
lang_code = {"עברית": "he", "אנגלית": "en", "צרפתית": "fr", "ספרדית": "es", "גרמנית": "de"}[language]

# בחירת גודל מודל Whisper
model_size = st.selectbox("📏 בחר גודל מודל Whisper", ["tiny", "base", "small", "medium", "large"], index=2)

# פונקציה להורדת אודיו מיוטיוב
def download_youtube_audio(url):
    try:
        yt = YouTube(url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        audio_stream.download(filename=temp_file.name)
        return temp_file.name
    except Exception as e:
        st.error(f"❌ שגיאה בהורדת הסרטון: {e}")
        return None

if uploaded_file or video_url:
    with st.spinner("⏳ מעבד את הקובץ..."):
        temp_file_path = None
        
        if uploaded_file:
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.write(uploaded_file.read())
            temp_file_path = temp_file.name
        elif video_url:
            temp_file_path = download_youtube_audio(video_url)
        
        if temp_file_path:
            # טעינת מודל התמלול
            model = whisper.load_model(model_size)
            result = model.transcribe(temp_file_path, language=lang_code)
            os.remove(temp_file_path)  # מחיקת הקובץ הזמני
            
            transcribed_text = result["text"]
            
            # אפשרות תרגום לשפה אחרת
            translate_to = st.selectbox("🌎 תרגם את התמלול לשפה", ["ללא", "אנגלית", "עברית", "צרפתית", "ספרדית", "גרמנית"], key="translate")
            if translate_to != "ללא":
                target_lang_code = {"עברית": "he", "אנגלית": "en", "צרפתית": "fr", "ספרדית": "es", "גרמנית": "de"}[translate_to]
                transcribed_text = GoogleTranslator(source="auto", target=target_lang_code).translate(transcribed_text)
            
            # הצגת תמלול
            st.markdown("<h3>📜 תמלול:</h3>", unsafe_allow_html=True)
            st.text_area("", transcribed_text, height=300)
            
            # יצירת קובצי ייצוא
            files = {
                "תמלול.txt": transcribed_text.encode(),
                "תמלול.json": json.dumps({"text": transcribed_text}, ensure_ascii=False).encode()
            }
            
            # הורדת קבצים
            col1, col2 = st.columns(2)
            with col1:
                for filename, data in files.items():
                    st.download_button(f"📥 הורד {filename}", data, filename, "text/plain")
            
            # הורדה בקובץ ZIP
            with col2:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for filename, data in files.items():
                        zf.writestr(filename, data)
                zip_buffer.seek(0)
                st.download_button("📥 הורד הכול כ-ZIP", zip_buffer, "תמלול.zip", "application/zip")
            
            st.success("✅ העיבוד הסתיים! ניתן להוריד את הקבצים.")
