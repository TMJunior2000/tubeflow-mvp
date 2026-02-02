import streamlit as st
import time

# Import Moduli
from modules.ai_engine import generate_script
from modules.asset_manager import get_hybrid_video, get_contextual_music
from modules.audio_engine import generate_voiceover_file
from modules.exporter import create_smart_package

st.set_page_config(page_title="TubeFlow AI", page_icon="⚡", layout="centered")

if 'credits' not in st.session_state: st.session_state['credits'] = 3
if 'generated_content' not in st.session_state: st.session_state['generated_content'] = None

# --- UI STYLES ---
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #fff; }
    div[data-testid="stForm"] { background: rgba(255,255,255,0.05); border-radius: 15px; padding: 20px; }
    </style>
""", unsafe_allow_html=True)

def main():
    st.title("⚡ TUBEFLOW AI")
    st.caption(f"Credits: {st.session_state['credits']}")

    with st.form("creator_form"):
        # 1. Concept (L'unico vero input necessario)
        topic = st.text_area("Video Concept", height=80, placeholder="Es. Un samurai solitario sotto la pioggia...")
        
        # 2. Settings Tecnici
        c1, c2 = st.columns(2)
        with c1:
            format_choice = st.radio("Format", ["9:16 (TikTok)", "16:9 (YouTube)"])
            orientation = "portrait" if "9:16" in format_choice else "landscape"
        with c2:
            voice_choice = st.selectbox("Voice", ["🇮🇹 Italiano (Diego)", "🇺🇸 English (Christopher)"])
            voice_id = "it-IT-DiegoNeural" if "Italiano" in voice_choice else "en-US-ChristopherNeural"
            
        c3, c4 = st.columns(2)
        with c3: use_voice = st.checkbox("Genera Voce", True)
        with c4: use_music = st.checkbox("Musica Contestuale", True)

        submit = st.form_submit_button("🚀 GENERATE")

    if submit:
        if not topic: st.stop()
        
        # Reset
        st.session_state['generated_content'] = None
        
        with st.status("🧠 AI Director is working...", expanded=True) as status:
            
            # 1. AI Analysis
            st.write("Analisi Contesto & Emozione...")
            script_data = generate_script(topic) # Ritorna dict completo
            
            if not script_data:
                st.error("Errore AI.")
                st.stop()
                
            scenes = script_data['scenes']
            audio_settings = script_data['audio_settings']
            
            # Mostra le decisioni dell'AI all'utente
            st.info(f"🎭 **Mood Rilevato:** Musica '{audio_settings['music_query']}' | Voce {audio_settings['voice_speed']}")

            # 2. Visual Hunt
            st.write("Ricerca Video...")
            final_scenes = []
            full_text = ""
            for s in scenes:
                full_text += s['voiceover'] + " "
                # Passiamo una vibe vuota perché ora usiamo keyword precise
                vid = get_hybrid_video(s['keyword'], "", orientation) 
                if vid:
                    s.update(vid)
                    s['video_link'] = vid['download']
                final_scenes.append(s)

            # 3. Audio Contextual
            music_url = None
            voice_path = None
            
            if use_music:
                st.write(f"Cercando brano: {audio_settings['music_query']}...")
                _, music_url = get_contextual_music(audio_settings['music_query'])
            
            if use_voice:
                st.write("Registrazione Voce...")
                voice_path = generate_voiceover_file(full_text, voice_id, audio_settings['voice_speed'])

            # 4. Packaging
            zip_data = create_smart_package(final_scenes, orientation, music_url, voice_path)
            
            st.session_state['generated_content'] = {
                "scenes": final_scenes,
                "zip_data": zip_data,
                "file_name": f"Video_{orientation}.zip"
            }
            status.update(label="Fatto!", state="complete")

    # --- RESULT VIEW ---
    if st.session_state['generated_content']:
        data = st.session_state['generated_content']
        st.success("Progetto Pronto.")
        
        for s in data['scenes']:
            with st.expander(f"Scene {s['scene_number']}: {s['keyword']}"):
                if s.get('preview'): st.video(s['preview'])
                st.write(s['voiceover'])
        
        st.download_button("⬇️ Scarica ZIP", data['zip_data'], data['file_name'], "application/zip", type="primary")

if __name__ == "__main__":
    main()