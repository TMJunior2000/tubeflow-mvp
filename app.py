import streamlit as st
import time

# Import Moduli
# Assicurati che esista il file __init__.py nella cartella modules!
from modules.ai_engine import generate_script
from modules.asset_manager import get_hybrid_video, get_background_music
from modules.audio_engine import generate_voiceover_file
from modules.exporter import create_smart_package

# Configurazione Pagina
st.set_page_config(page_title="TubeFlow AI", page_icon="⚡", layout="centered")

# --- 1. GESTIONE STATO (MEMORIA) ---
# Qui salviamo i dati per non perderli quando clicchi "Download"
if 'credits' not in st.session_state:
    st.session_state['credits'] = 3
if 'generated_content' not in st.session_state:
    st.session_state['generated_content'] = None # Qui salveremo lo ZIP e le info

# --- CSS STYLES ---
st.markdown("""
    <style>
    .stApp { background-color: #050505; background-image: radial-gradient(circle at 50% 0%, #1a1a2e 0%, #050505 60%); }
    .hero-title { font-family: 'Inter', sans-serif; font-size: 3rem; font-weight: 800; background: -webkit-linear-gradient(0deg, #00f2ea, #ff0050); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; }
    .credit-badge { text-align: center; font-family: monospace; color: #00f2ea; background: rgba(0, 242, 234, 0.1); padding: 5px 15px; border-radius: 20px; border: 1px solid rgba(0, 242, 234, 0.3); margin: 10px auto 30px auto; width: fit-content; }
    div[data-testid="stForm"] { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 24px; padding: 2rem; backdrop-filter: blur(10px); }
    .stButton > button { background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%); color: #000; font-weight: bold; border: none; border-radius: 12px; height: 50px; font-size: 1.1rem; width: 100%; }
    </style>
""", unsafe_allow_html=True)

def main():
    # HERO & CREDITS
    st.markdown('<div class="hero-title">TUBEFLOW AI</div>', unsafe_allow_html=True)
    
    credit_placeholder = st.empty()
    def show_credits():
        val = st.session_state['credits']
        credit_placeholder.markdown(f'<div class="credit-badge">⚡ CREDITS AVAILABLE: {val}</div>', unsafe_allow_html=True)
    show_credits()

    # --- INPUT FORM ---
    with st.form("creator_form"):
        st.markdown("**1. VIDEO CONCEPT**")
        topic = st.text_area("Di cosa parla il video?", height=80, placeholder="Es. L'avventura epica di un pinguino...")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**2. STYLE**")
            vibe = st.selectbox("Vibe", ["Fast Paced", "Dark Cinematic", "Luxury", "Minimalist", "Nature Documentary"], label_visibility="collapsed")
        with c2:
            st.markdown("**3. FORMAT**")
            format_choice = st.radio("Ratio", ["9:16 (TikTok/Reels)", "16:9 (YouTube)"], label_visibility="collapsed")
            orientation = "portrait" if "9:16" in format_choice else "landscape"

        st.markdown("---")
        st.markdown("**4. AUDIO OPTIONS**")
        
        # Le opzioni audio devono essere visibili SUBITO
        c3, c4 = st.columns(2)
        with c3:
            use_voice = st.checkbox("🎙️ Generate Voiceover", value=True)
            use_music = st.checkbox("🎵 Add Background Music", value=True) # Default True per testare
            
        with c4:
            voice_options = {
                "🇮🇹 Italiano (Diego)": "it-IT-DiegoNeural",
                "🇺🇸 English (Christopher)": "en-US-ChristopherNeural"
            }
            selected_label = st.selectbox("Lingua Voce", list(voice_options.keys()), label_visibility="collapsed")
            voice_id = voice_options[selected_label]

        submit = st.form_submit_button("⚡ GENERATE PLAN")

    # --- LOGICA DI GENERAZIONE (SOLO SE SI CLICCA IL BOTTONE) ---
    if submit:
        # 1. Validazione
        if not topic:
            st.warning("⚠️ Scrivi un argomento!")
            st.stop()
        if st.session_state['credits'] <= 0:
            st.error("❌ Crediti esauriti.")
            st.stop()

        # 2. Consumo Credito
        st.session_state['credits'] -= 1
        show_credits()
        
        # 3. Reset dello stato precedente (pulizia)
        st.session_state['generated_content'] = None 

        # 4. Esecuzione Workflow
        with st.status("🔮 Magic in progress...", expanded=True) as status:
            
            # A. AI Script
            st.write("🧠 Designing Script (Gemini 1.5)...")
            scenes = generate_script(topic, vibe)
            if not scenes:
                status.update(label="❌ AI Error.", state="error")
                st.session_state['credits'] += 1 # Rimborso
                st.stop()

            # B. Asset Hunt (Video)
            st.write(f"🎥 Hunting Visuals ({orientation.upper()})...")
            final_scenes = []
            full_text = ""
            
            for s in scenes:
                full_text += s['voiceover'] + " "
                # Logica Breadcrumb + Parallela (Pexels/Pixabay)
                vid = get_hybrid_video(s['keyword'], vibe, orientation)
                
                if vid:
                    s['download'] = vid['download'] # Link al file HD
                    s['preview'] = vid['preview']   # Link leggero
                    s['source'] = vid.get('source', 'Unknown')
                    s['match_type'] = vid.get('match_type', 'Found')
                    s['video_link'] = vid['download'] # Compatibilità Exporter
                else:
                    s['download'] = None
                    s['preview'] = None
                    s['source'] = "Not Found"
                    s['match_type'] = "🔴 MISSING"
                
                final_scenes.append(s)

            # C. Audio Assets
            music_url = None
            voice_path = None

            if use_music:
                st.write(f"🎵 Finding Music for vibe: {vibe}...")
                music_data = get_background_music(vibe)
                if music_data:
                    # music_data è (page_url, mp3_url)
                    music_url = music_data[1] 
                    st.write("✅ Music Track Found!")
                else:
                    st.warning("⚠️ Music API returned no results (Rate Limit?).")

            if use_voice and voice_id:
                st.write("🎙️ Recording Neural Voiceover...")
                voice_path = generate_voiceover_file(full_text, voice_id)

            # D. Packaging (ZIP + XML)
            st.write("📦 Creating Smart Package...")
            # Qui chiamiamo l'exporter aggiornato che scarica i file
            zip_data = create_smart_package(final_scenes, orientation, music_url, voice_path)
            
            # 5. SALVATAGGIO IN MEMORIA (PERSISTENZA)
            # Salviamo tutto in session_state così sopravvive al reload del download
            st.session_state['generated_content'] = {
                "scenes": final_scenes,
                "zip_data": zip_data,
                "format_label": format_choice,
                "file_name": f"TubeFlow_{orientation}.zip"
            }
            
            status.update(label="✅ GENERATION COMPLETE", state="complete")

    # --- VISUALIZZAZIONE RISULTATI (FUORI DAL FORM) ---
    # Questo blocco viene eseguito ad ogni reload se c'è qualcosa in memoria
    if st.session_state['generated_content']:
        content = st.session_state['generated_content']
        scenes = content['scenes']
        
        st.markdown("---")
        st.success("✅ Project Ready (Saved in Memory)")

        # Preview Cards
        for s in scenes:
            with st.expander(f"Scene {s['scene_number']}: {s['keyword']} ({s.get('match_type')})"):
                c1, c2 = st.columns([1, 2])
                with c1:
                    if s.get('preview'):
                        if ".mp4" in s['preview'] or ".webm" in s['preview']:
                            st.video(s['preview'])
                        else:
                            st.image(s['preview'], use_container_width=True)
                    else:
                        st.error("No visual found")
                with c2:
                    st.caption(f"Source: {s.get('source')}")
                    st.write(f"**Script:** {s['voiceover']}")

        # DOWNLOAD BUTTON (Ora funziona senza resettare l'app)
        st.download_button(
            label=f"⬇️ DOWNLOAD {content['format_label']} PACK",
            data=content['zip_data'],
            file_name=content['file_name'],
            mime="application/zip",
            type="primary"
        )
        
        # Bottone per pulire e ricominciare
        if st.button("🔄 Start New Project"):
            st.session_state['generated_content'] = None
            st.rerun()

if __name__ == "__main__":
    main()