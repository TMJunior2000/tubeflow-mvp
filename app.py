import streamlit as st
import time

# Import Moduli
from modules.ai_engine import generate_script
from modules.asset_manager import get_hybrid_video, get_pixabay_audio
from modules.audio_engine import generate_voiceover_file
from modules.exporter import create_smart_package

st.set_page_config(page_title="TubeFlow AI", page_icon="⚡", layout="centered")

# --- CSS STYLES (Invariato) ---
st.markdown("""
    <style>
    .stApp { background-color: #050505; background-image: radial-gradient(circle at 50% 0%, #1a1a2e 0%, #050505 60%); color: #fff; }
    div[data-testid="stForm"] { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 24px; padding: 2rem; }
    </style>
""", unsafe_allow_html=True)

if 'credits' not in st.session_state: st.session_state['credits'] = 3
if 'generated_content' not in st.session_state: st.session_state['generated_content'] = None

def main():
    st.title("⚡ TUBEFLOW AI")
    st.caption(f"Credits Available: {st.session_state['credits']}")

    with st.form("creator_form"):
        topic = st.text_area("Video Concept", height=80, placeholder="Es. Samurai sotto la pioggia...")
        
        c1, c2 = st.columns(2)
        with c1:
            format_choice = st.radio("Format", ["9:16 (Reels)", "16:9 (YouTube)"], label_visibility="collapsed")
            orientation = "portrait" if "9:16" in format_choice else "landscape"
        with c2:
            st.caption("Voice Language")
            voice_choice = st.selectbox("L", ["🇮🇹 Italiano", "🇺🇸 English"], label_visibility="collapsed")
            voice_id = "it-IT-DiegoNeural" if "Italiano" in voice_choice else "en-US-ChristopherNeural"

        c3, c4 = st.columns(2)
        with c3: use_voice = st.checkbox("Genera Voce", True)
        with c4: use_music = st.checkbox("Cerca Musica", True)

        submit = st.form_submit_button("⚡ GENERATE")

    if submit:
        if not topic: st.warning("Scrivi qualcosa!"); st.stop()
        st.session_state['credits'] -= 1
        st.session_state['generated_content'] = None

        with st.status("🔮 AI Director working...", expanded=True) as status:
            
            # 1. AI SCRIPT
            st.write("🧠 Generazione Script & Mood...")
            script_data = generate_script(topic)
            if not script_data: st.error("AI Error"); st.stop()
            
            scenes = script_data['scenes']
            audio_settings = script_data['audio_settings']
            genre = audio_settings.get('pixabay_genre', 'cinematic')
            mood = audio_settings.get('pixabay_mood', 'epic')
            speed = audio_settings.get('voice_speed', '+0%')

            st.info(f"Mood: {genre} / {mood} | Speed: {speed}")

            # 2. VIDEO HUNT (Pexels vs Pixabay)
            st.write("🎥 Ricerca Clip Video...")
            final_scenes = []
            full_text = ""
            for s in scenes:
                full_text += s['voiceover'] + " "
                vid = get_hybrid_video(s['keyword'], "", orientation)
                if vid:
                    s.update(vid)
                    s['video_link'] = vid['download']
                final_scenes.append(s)

            # 3. AUDIO (Safe Search)
            music_url = None
            voice_path = None

            if use_music:
                st.write(f"🎵 Ricerca Audio API ({genre} {mood})...")
                # get_pixabay_audio ORA NON USA HEADERS FAKE (Così evita 403 in ricerca)
                page_link, mp3_link = get_pixabay_audio(genre, mood)
                
                if mp3_link:
                    music_url = mp3_link
                    # NON usiamo st.audio(url) qui per evitare 403 nel browser!
                    st.success(f"✅ Musica Trovata! Sarà inclusa nello ZIP.")
                else:
                    st.warning("⚠️ Musica non trovata o errore API.")

            if use_voice:
                st.write("🎙️ Sintesi Vocale...")
                voice_path = generate_voiceover_file(full_text, voice_id, speed)

            # 4. ZIP PACKAGING (Download Reale Anti-403)
            st.write("📦 Download Assets & Creazione ZIP...")
            # Qui avviene il download vero usando la funzione 'download_asset_to_memory'
            zip_data = create_smart_package(final_scenes, orientation, music_url, voice_path)
            
            st.session_state['generated_content'] = {
                "scenes": final_scenes,
                "zip_data": zip_data,
                "file_name": f"Project_{orientation}.zip"
            }
            status.update(label="✅ COMPLETATO!", state="complete")

    # RESULT VIEW
    if st.session_state['generated_content']:
        data = st.session_state['generated_content']
        st.success("Progetto Pronto per il Download.")
        
        # Anteprima Video (Solo Player HTML5 standard)
        for s in data['scenes']:
            with st.expander(f"Scene {s['scene_number']}: {s['keyword']}"):
                if s.get('preview'): 
                    st.video(s['preview']) # I link preview tiny/small di solito non hanno 403
                st.write(s['voiceover'])

        st.download_button(
            label="⬇️ SCARICA PACCHETTO COMPLETO (ZIP)",
            data=data['zip_data'],
            file_name=data['file_name'],
            mime="application/zip",
            type="primary"
        )

if __name__ == "__main__":
    main()