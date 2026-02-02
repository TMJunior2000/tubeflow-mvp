import streamlit as st
import time

# --- IMPORT MODULI (Logica Aggiornata) ---
from modules.ai_engine import generate_script
from modules.asset_manager import get_hybrid_video, get_pixabay_audio
from modules.audio_engine import generate_voiceover_file
from modules.exporter import create_smart_package

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="TubeFlow AI", page_icon="⚡", layout="centered")

# --- GESTIONE STATO ---
if 'credits' not in st.session_state: st.session_state['credits'] = 3
if 'generated_content' not in st.session_state: st.session_state['generated_content'] = None

# --- CSS STYLES (IL TUO DESIGN PREFERITO) ---
st.markdown("""
    <style>
    /* Dark Theme Background */
    .stApp { background-color: #050505; background-image: radial-gradient(circle at 50% 0%, #1a1a2e 0%, #050505 60%); color: #fff; }
    
    /* Hero Title */
    .hero-title { 
        font-family: 'Inter', sans-serif; 
        font-size: 3rem; 
        font-weight: 800; 
        background: -webkit-linear-gradient(0deg, #00f2ea, #ff0050); 
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        text-align: center; 
        margin-bottom: 0px;
    }
    
    /* Credits Badge */
    .credit-badge { 
        text-align: center; 
        font-family: monospace; 
        color: #00f2ea; 
        background: rgba(0, 242, 234, 0.1); 
        padding: 5px 15px; 
        border-radius: 20px; 
        border: 1px solid rgba(0, 242, 234, 0.3); 
        margin: 10px auto 30px auto; 
        width: fit-content; 
    }
    
    /* Glassmorphism Form */
    div[data-testid="stForm"] { 
        background: rgba(255, 255, 255, 0.03); 
        border: 1px solid rgba(255, 255, 255, 0.1); 
        border-radius: 24px; 
        padding: 2rem; 
        backdrop-filter: blur(10px); 
    }
    
    /* Buttons */
    .stButton > button { 
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%); 
        color: #000; 
        font-weight: bold; 
        border: none; 
        border-radius: 12px; 
        height: 50px; 
        font-size: 1.1rem; 
        width: 100%; 
    }
    
    /* Expander Styling */
    .streamlit-expanderHeader {
        background-color: rgba(255,255,255,0.05);
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    # HERO SECTION
    st.markdown('<div class="hero-title">TUBEFLOW AI</div>', unsafe_allow_html=True)
    
    # Credits UI
    credit_placeholder = st.empty()
    def update_credits_ui():
        val = st.session_state['credits']
        credit_placeholder.markdown(f'<div class="credit-badge">⚡ CREDITS AVAILABLE: {val}</div>', unsafe_allow_html=True)
    update_credits_ui()

    # --- INPUT FORM ---
    with st.form("creator_form"):
        st.markdown("**1. VIDEO CONCEPT**")
        topic = st.text_area(
            "Di cosa parla il video?", 
            height=80, 
            placeholder="Es. Samurai sotto la pioggia (L'IA userà Pexels e Pixabay in modo intelligente...)"
        )
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**2. FORMAT**")
            format_choice = st.radio("Ratio", ["9:16 (TikTok/Reels)", "16:9 (YouTube)"], label_visibility="collapsed")
            orientation = "portrait" if "9:16" in format_choice else "landscape"
        
        with c2:
            st.markdown("**3. VOICE LANGUAGE**")
            voice_options = {
                "🇮🇹 Italiano (Diego)": "it-IT-DiegoNeural",
                "🇺🇸 English (Christopher)": "en-US-ChristopherNeural"
            }
            selected_label = st.selectbox("Lingua", list(voice_options.keys()), label_visibility="collapsed")
            voice_id = voice_options[selected_label]

        st.markdown("---")
        
        c3, c4 = st.columns(2)
        with c3: use_voice = st.checkbox("🎙️ Generate Voiceover", value=True) 
        with c4: use_music = st.checkbox("🎵 Auto-Match Music", value=True)

        submit = st.form_submit_button("⚡ GENERATE MAGIC")

    # --- LOGICA BACKEND ---
    if submit:
        if not topic:
            st.warning("⚠️ Scrivi un argomento!")
            st.stop()
        if st.session_state['credits'] <= 0:
            st.error("❌ Crediti esauriti.")
            st.stop()

        st.session_state['credits'] -= 1
        update_credits_ui()
        st.session_state['generated_content'] = None

        with st.status("🔮 AI Director is working...", expanded=True) as status:
            
            # 1. AI Analysis
            st.write("🧠 Analyzing Sentiment & Structure...")
            script_data = generate_script(topic)
            
            if not script_data:
                status.update(label="❌ AI Error.", state="error")
                st.session_state['credits'] += 1
                st.stop()

            scenes = script_data['scenes']
            audio_settings = script_data['audio_settings']
            
            # Estrazione Settings
            genre = audio_settings.get('pixabay_genre', 'cinematic')
            mood = audio_settings.get('pixabay_mood', 'epic')
            speed = audio_settings.get('voice_speed', '+0%')
            
            st.info(f"🎭 **Mood:** {genre} / {mood} | **Voice Speed:** {speed}")

            # 2. Visual Hunt (Pexels vs Pixabay)
            st.write(f"🎥 Hunting Visuals ({orientation.upper()})...")
            final_scenes = []
            full_text = ""
            
            for s in scenes:
                full_text += s['voiceover'] + " "
                # Logica ibrida aggiornata
                vid = get_hybrid_video(s['keyword'], "", orientation)
                
                if vid:
                    s.update(vid)
                    s['video_link'] = vid['download']
                else:
                    s['download'] = None; s['preview'] = None; s['source'] = "Not Found"
                
                final_scenes.append(s)

            # 3. Audio Search (No 403 Logic)
            music_url = None
            voice_path = None

            if use_music:
                st.write(f"🎵 Searching Audio API ({genre} {mood})...")
                # La funzione get_pixabay_audio aggiornata ora NON usa headers fake (evita 403 in ricerca)
                page_link, mp3_link = get_pixabay_audio(genre, mood)
                
                if mp3_link:
                    music_url = mp3_link
                    # NON mostriamo il player qui per evitare chiamate browser cross-origin
                    st.success(f"✅ Music Found! Ready for ZIP download.")
                else:
                    st.warning("⚠️ Music not found or API limit. (Check console for error)")

            if use_voice:
                st.write("🎙️ Synthesizing Voice...")
                voice_path = generate_voiceover_file(full_text, voice_id, speed)

            # 4. Packaging (Download in RAM)
            st.write("📦 Downloading Assets to Server & Zipping...")
            # create_smart_package ora scarica i file fisicamente
            zip_data = create_smart_package(final_scenes, orientation, music_url, voice_path)
            
            st.session_state['generated_content'] = {
                "scenes": final_scenes,
                "zip_data": zip_data,
                "format_label": format_choice,
                "file_name": f"TubeFlow_{orientation}.zip",
                "mood_info": f"{genre} / {mood}"
            }
            
            status.update(label="✅ GENERATION COMPLETE", state="complete")

    # --- RESULT VIEW ---
    if st.session_state['generated_content']:
        content = st.session_state['generated_content']
        scenes = content['scenes']
        
        st.markdown("---")
        st.success(f"✅ Project Ready! Mood: {content['mood_info']}")

        # Preview Cards
        for s in scenes:
            # Colore Badge match
            match_type = s.get('match_type', 'UNKNOWN')
            color = "green" if "EXACT" in match_type else "orange"
            
            with st.expander(f"Scene {s['scene_number']}: {s['keyword']} :{color}[{match_type}]"):
                c1, c2 = st.columns([1, 2])
                with c1:
                    if s.get('preview'):
                        st.video(s['preview'])
                    else:
                        st.error("No visual found")
                with c2:
                    st.caption(f"Source: **{s.get('source', 'Unknown')}**")
                    st.write(f"**Script:** {s['voiceover']}")

        # DOWNLOAD BUTTON
        st.download_button(
            label=f"⬇️ DOWNLOAD {content['format_label']} PACK",
            data=content['zip_data'],
            file_name=content['file_name'],
            mime="application/zip",
            type="primary"
        )
        
        if st.button("🔄 Start New Project"):
            st.session_state['generated_content'] = None
            st.rerun()

if __name__ == "__main__":
    main()