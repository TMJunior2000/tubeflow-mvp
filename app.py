import streamlit as st
from modules.ai_engine import generate_script
from modules.asset_manager import get_hybrid_video
from modules.audio_engine import generate_voiceover_file
from modules.exporter import create_smart_package

st.set_page_config(page_title="TubeFlow v3", page_icon="⚡", layout="centered")

# Inizializzazione Session State
if 'credits' not in st.session_state: st.session_state['credits'] = 20 # Allineato a quota Free 2026

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #fff; }
    .hero-title { font-size: 3rem; font-weight: 800; background: linear-gradient(90deg, #00f2ea, #ff0050); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; }
    div[data-testid="stForm"] { background: rgba(255, 255, 255, 0.05); border-radius: 20px; padding: 20px; border: 1px solid #333; }
    </style>
""", unsafe_allow_html=True)

def main():
    st.markdown('<div class="hero-title">TUBEFLOW v3</div>', unsafe_allow_html=True)
    st.caption(f"📅 Quota Status: {st.session_state['credits']}/20 requests remaining today")

    with st.form("creator_form"):
        topic = st.text_area("Cosa vuoi creare?", placeholder="Esempio: Video noir di 3 clip su un tradimento...")
        c1, c2 = st.columns(2)
        with c1:
            format_choice = st.radio("Formato", ["9:16 (TikTok/Reels)", "16:9 (YouTube)"])
            orientation = "portrait" if "9:16" in format_choice else "landscape"
        with c2:
            voice_choice = st.selectbox("Voce AI", ["Diego (IT)", "Christopher (EN)"])
            voice_id = "it-IT-DiegoNeural" if "Diego" in voice_choice else "en-US-ChristopherNeural"
        
        submit = st.form_submit_button("⚡ GENERA PROGETTO")

    if submit and topic:
        with st.status("🎬 Director at work...", expanded=True) as status:
            
            # 1. AI SCRIPTING (Gemini 3)
            st.write("🧠 Ragionamento Gemini 3 Flash...")
            script_data = generate_script(topic)
            if not script_data: st.stop()
            
            # 2. VIDEO HUNTING
            st.write("🎥 Ricerca Clip Sniper...")
            used_urls = []
            final_scenes = []
            for s in script_data['scenes']:
                vid = get_hybrid_video(s['keyword'], orientation, excluded_urls=used_urls)
                if vid:
                    s.update(vid)
                    used_urls.append(vid['download'])
                final_scenes.append(s)
            
            # 3. VOICE GENERATION
            st.write("🎙️ Sintesi Vocale...")
            full_text = " ".join([s['voiceover'] for s in final_scenes])
            v_speed = script_data['voice_settings']['voice_speed']
            v_path = generate_voiceover_file(full_text, voice_id, v_speed)

            # 4. EXPORT
            st.write("📦 Creazione Pacchetto ZIP...")
            zip_data = create_smart_package(final_scenes, orientation, None, v_path)
            
            st.session_state['credits'] -= 1
            status.update(label="✅ PROGETTO PRONTO!", state="complete")

            st.download_button("⬇️ SCARICA ZIP PER DAVINCI/PREMIERE", zip_data, f"TubeFlow_{orientation}.zip", "application/zip")

if __name__ == "__main__":
    main()