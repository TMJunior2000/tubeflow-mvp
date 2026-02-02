import streamlit as st
import time

# Import Moduli
# Assicurati che i file in 'modules/' siano aggiornati con le versioni mandate prima!
from modules.ai_engine import generate_script
from modules.asset_manager import get_hybrid_video, get_contextual_music
from modules.audio_engine import generate_voiceover_file
from modules.exporter import create_smart_package

# Configurazione Pagina
st.set_page_config(page_title="TubeFlow AI", page_icon="⚡", layout="centered")

# --- 1. GESTIONE STATO (MEMORIA) ---
if 'credits' not in st.session_state: st.session_state['credits'] = 3
if 'generated_content' not in st.session_state: st.session_state['generated_content'] = None

# --- 2. CSS STYLING (IL TUO STILE PREFERITO) ---
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
    
    # Credits (funzione helper per aggiornare)
    credit_placeholder = st.empty()
    def update_credits_ui():
        val = st.session_state['credits']
        credit_placeholder.markdown(f'<div class="credit-badge">⚡ CREDITS AVAILABLE: {val}</div>', unsafe_allow_html=True)
    update_credits_ui()

    # --- INPUT FORM ---
    with st.form("creator_form"):
        st.markdown("**1. VIDEO CONCEPT**")
        # Placeholder educativo
        topic = st.text_area(
            "Di cosa parla il video?", 
            height=80, 
            placeholder="Es. Un samurai solitario sotto la pioggia (L'IA deciderà stile, musica e ritmo da sola...)"
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
        
        # Opzioni Checkbox
        c3, c4 = st.columns(2)
        with c3:
            use_voice = st.checkbox("🎙️ Generate Voiceover", value=True) 
        with c4:
            use_music = st.checkbox("🎵 Auto-Match Music", value=True)

        submit = st.form_submit_button("⚡ GENERATE MAGIC")

    # --- LOGICA DI BACKEND ---
    if submit:
        if not topic:
            st.warning("⚠️ Scrivi un argomento!")
            st.stop()
        if st.session_state['credits'] <= 0:
            st.error("❌ Crediti esauriti.")
            st.stop()

        # Consumo Credito
        st.session_state['credits'] -= 1
        update_credits_ui()
        st.session_state['generated_content'] = None # Reset memoria

        with st.status("🔮 AI Director is working...", expanded=True) as status:
            
            # STEP 1: AI Brain (Senza Vibe manuale)
            st.write("🧠 Analyzing Sentiment & Structure...")
            script_data = generate_script(topic) # Chiamata al nuovo engine
            
            if not script_data:
                status.update(label="❌ AI Error.", state="error")
                st.session_state['credits'] += 1
                st.stop()

            # Estrazione Dati
            scenes = script_data['scenes']
            audio_settings = script_data['audio_settings']
            
            # Mostriamo all'utente cosa ha deciso l'IA
            st.info(f"🎭 **Mood Rilevato:** Musica '{audio_settings['music_query']}' | Voce {audio_settings['voice_speed']}")

            # STEP 2: Asset Hunt
            st.write(f"🎥 Hunting Visuals ({orientation.upper()})...")
            final_scenes = []
            full_text = ""
            
            for s in scenes:
                full_text += s['voiceover'] + " "
                # Passiamo stringa vuota per vibe, l'engine ora usa keywords precise
                vid = get_hybrid_video(s['keyword'], "", orientation)
                
                if vid:
                    s.update(vid) # Unisce i dati trovati (preview, download, source)
                    s['video_link'] = vid['download'] # Per compatibilità exporter
                else:
                    s['download'] = None
                    s['preview'] = None
                    s['source'] = "Not Found"
                
                final_scenes.append(s)

            # STEP 3: Audio Search (API Reale)
            music_url = None
            voice_path = None

            if use_music:
                st.write(f"🎵 Searching Pixabay Audio: '{audio_settings['music_query']}'...")
                # Chiama la nuova funzione get_contextual_music
                music_res = get_contextual_music(audio_settings['music_query'])
                if music_res:
                    music_url = music_res[1] # Prende il link mp3
                    st.write("✅ Music Track Found!")
                else:
                    st.warning("⚠️ Music not found (API Rate Limit?).")

            if use_voice:
                st.write("🎙️ Synthesizing Neural Voice...")
                # Passa la velocità decisa dall'IA (+10%, -10%, ecc.)
                voice_path = generate_voiceover_file(full_text, voice_id, audio_settings['voice_speed'])

            # STEP 4: Packaging
            st.write("📦 Building ZIP & XML...")
            zip_data = create_smart_package(final_scenes, orientation, music_url, voice_path)
            
            # Salvataggio Stato
            st.session_state['generated_content'] = {
                "scenes": final_scenes,
                "zip_data": zip_data,
                "format_label": format_choice,
                "file_name": f"TubeFlow_{orientation}.zip",
                "mood_info": audio_settings # Salviamo anche il mood per mostrarlo
            }
            
            status.update(label="✅ GENERATION COMPLETE", state="complete")

    # --- RESULT VIEW (Persistente) ---
    if st.session_state['generated_content']:
        content = st.session_state['generated_content']
        scenes = content['scenes']
        
        st.markdown("---")
        st.success(f"✅ Project Ready! Mood: {content['mood_info']['music_query']}")

        # Preview Cards
        for s in scenes:
            # Mostra badge colorati in base al tipo di match
            match_color = "green" if "EXACT" in s.get('match_type', '') else "orange"
            with st.expander(f"Scene {s['scene_number']}: {s['keyword']} :{match_color}[{s.get('match_type')}]"):
                c1, c2 = st.columns([1, 2])
                with c1:
                    if s.get('preview'):
                        st.video(s['preview'])
                    else:
                        st.error("No visual found")
                with c2:
                    st.caption(f"Source: {s.get('source')}")
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