import streamlit as st
import time

# Import Moduli
from modules.ai_engine import generate_script
from modules.asset_manager import get_hybrid_video, get_pixabay_audio
from modules.audio_engine import generate_voiceover_file
from modules.exporter import create_smart_package

# Configurazione Pagina
st.set_page_config(page_title="TubeFlow AI", page_icon="⚡", layout="centered")

# --- GESTIONE STATO ---
if 'credits' not in st.session_state: st.session_state['credits'] = 3
if 'generated_content' not in st.session_state: st.session_state['generated_content'] = None

# --- CSS STYLES ---
st.markdown("""
    <style>
    .stApp { background-color: #050505; background-image: radial-gradient(circle at 50% 0%, #1a1a2e 0%, #050505 60%); color: #fff; }
    .hero-title { font-family: 'Inter', sans-serif; font-size: 3rem; font-weight: 800; background: -webkit-linear-gradient(0deg, #00f2ea, #ff0050); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 0px;}
    .credit-badge { text-align: center; font-family: monospace; color: #00f2ea; background: rgba(0, 242, 234, 0.1); padding: 5px 15px; border-radius: 20px; border: 1px solid rgba(0, 242, 234, 0.3); margin: 10px auto 30px auto; width: fit-content; }
    div[data-testid="stForm"] { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 24px; padding: 2rem; backdrop-filter: blur(10px); }
    .stButton > button { background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%); color: #000; font-weight: bold; border: none; border-radius: 12px; height: 50px; font-size: 1.1rem; width: 100%; }
    </style>
""", unsafe_allow_html=True)

def main():
    st.markdown('<div class="hero-title">TUBEFLOW AI</div>', unsafe_allow_html=True)
    
    credit_placeholder = st.empty()
    def update_credits_ui():
        val = st.session_state['credits']
        credit_placeholder.markdown(f'<div class="credit-badge">⚡ CREDITS AVAILABLE: {val}</div>', unsafe_allow_html=True)
    update_credits_ui()

    with st.form("creator_form"):
        st.markdown("**1. VIDEO CONCEPT**")
        topic = st.text_area("Di cosa parla il video?", height=80, placeholder="Es. Un samurai solitario sotto la pioggia...")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**2. FORMAT**")
            format_choice = st.radio("Ratio", ["9:16 (TikTok/Reels)", "16:9 (YouTube)"], label_visibility="collapsed")
            orientation = "portrait" if "9:16" in format_choice else "landscape"
        with c2:
            st.markdown("**3. VOICE LANGUAGE**")
            voice_options = {"🇮🇹 Italiano (Diego)": "it-IT-DiegoNeural", "🇺🇸 English (Christopher)": "en-US-ChristopherNeural"}
            selected_label = st.selectbox("Lingua", list(voice_options.keys()), label_visibility="collapsed")
            voice_id = voice_options[selected_label]

        st.markdown("---")
        c3, c4 = st.columns(2)
        with c3: use_voice = st.checkbox("🎙️ Generate Voiceover", value=True) 
        with c4: use_music = st.checkbox("🎵 Auto-Match Music", value=True)

        submit = st.form_submit_button("⚡ GENERATE MAGIC")

    if submit:
        if not topic: st.warning("⚠️ Scrivi un argomento!"); st.stop()
        if st.session_state['credits'] <= 0: st.error("❌ Crediti esauriti."); st.stop()

        st.session_state['credits'] -= 1
        update_credits_ui()
        st.session_state['generated_content'] = None

        with st.status("🔮 AI Director is working...", expanded=True) as status:
            
            # STEP 1: AI Brain
            st.write("🧠 Analyzing Sentiment & Structure...")
            script_data = generate_script(topic)
            
            if not script_data:
                status.update(label="❌ AI Error.", state="error")
                st.session_state['credits'] += 1
                st.stop()

            scenes = script_data['scenes']
            audio_settings = script_data['audio_settings']
            
            # --- FIX: Ora usiamo i nomi corretti del dizionario ---
            genre = audio_settings.get('pixabay_genre', 'ambient')
            mood = audio_settings.get('pixabay_mood', 'contemplative')
            speed = audio_settings.get('voice_speed', '+0%')
            
            st.info(f"🎭 **Mood Rilevato:** Genre '{genre}' + Mood '{mood}' | Voce {speed}")

            # STEP 2: Visual Hunt
            st.write(f"🎥 Hunting Visuals ({orientation.upper()})...")
            final_scenes = []
            full_text = ""
            
            for s in scenes:
                full_text += s['voiceover'] + " "
                # Ricerca video (passiamo stringa vuota per vibe perché usiamo keyword)
                vid = get_hybrid_video(s['keyword'], "", orientation)
                
                if vid:
                    s.update(vid)
                    s['video_link'] = vid['download']
                else:
                    s['download'] = None; s['preview'] = None; s['source'] = "Not Found"
                
                final_scenes.append(s)

            # STEP 3: Audio Contextual
            music_url = None
            voice_path = None

            if use_music:
                st.write(f"🎵 Searching Pixabay Audio: Genre '{genre}' Mood '{mood}'...")
                # Chiamiamo la funzione corretta in asset_manager
                music_res = get_pixabay_audio(genre, mood)
                
                if music_res and music_res[1]:
                    music_url = music_res[1]
                    st.success(f"✅ Track Found: [Listen]({music_url})")
                else:
                    st.warning("⚠️ Music API limit or empty. Using fallback.")
                    music_url = "https://cdn.pixabay.com/download/audio/2022/03/24/audio_1969a58943.mp3"

            if use_voice:
                st.write(f"🎙️ Recording (Speed: {speed})...")
                voice_path = generate_voiceover_file(full_text, voice_id, speed)

            # STEP 4: Packaging
            st.write("📦 Building ZIP & XML...")
            zip_data = create_smart_package(final_scenes, orientation, music_url, voice_path)
            
            st.session_state['generated_content'] = {
                "scenes": final_scenes, "zip_data": zip_data, 
                "format_label": format_choice, "file_name": f"TubeFlow_{orientation}.zip",
                "mood_info": f"{genre} / {mood}"
            }
            status.update(label="✅ GENERATION COMPLETE", state="complete")

    if st.session_state['generated_content']:
        content = st.session_state['generated_content']
        st.markdown("---")
        st.success(f"✅ Project Ready! Mood: {content['mood_info']}")

        for s in content['scenes']:
            with st.expander(f"Scene {s['scene_number']}: {s['keyword']}"):
                c1, c2 = st.columns([1, 2])
                with c1:
                    if s.get('preview'): st.video(s['preview'])
                    else: st.error("No visual")
                with c2:
                    st.caption(f"Source: {s.get('source')}")
                    st.write(f"**Script:** {s['voiceover']}")

        st.download_button(f"⬇️ DOWNLOAD {content['format_label']} PACK", content['zip_data'], content['file_name'], "application/zip", type="primary")
        if st.button("🔄 Start New Project"): st.session_state['generated_content'] = None; st.rerun()

if __name__ == "__main__":
    main()