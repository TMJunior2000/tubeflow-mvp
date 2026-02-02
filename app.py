import streamlit as st
import os

# Importazione moduli locali
from modules.ai_engine import generate_script
from modules.asset_manager import get_hybrid_video, get_background_music
from modules.audio_engine import generate_voiceover_file
from modules.exporter import create_smart_package

# Configurazione Pagina
st.set_page_config(page_title="TubeFlow AI | Pro", page_icon="🎬", layout="wide")

# CSS Moderno
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fff; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; }
    div[data-testid="stStatusWidget"] { border: 1px solid #333; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

def main():
    # --- SIDEBAR: Configurazione ---
    with st.sidebar:
        st.header("⚙️ Setup")
        st.info("Questo tool usa il modello 'Bring Your Own Key' per scalare.")
        
        user_api_key = st.text_input("Gemini API Key", type="password", help="Necessaria per generare lo script")
        if not user_api_key:
            st.warning("Inserisci API Key per iniziare.")
            st.markdown("[Ottieni Key Gratis](https://aistudio.google.com/)")
        
        st.divider()
        st.caption("✅ Hybrid Search: Pexels + Pixabay")
        st.caption("✅ Audio Engine: EdgeTTS + Pixabay Music")

    # --- HERO SECTION ---
    st.title("🎬 TubeFlow AI")
    st.subheader("Automated Video Production for Social Media")

    # --- INPUT FORM ---
    with st.form("main_form"):
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            topic = st.text_input("Topic", placeholder="Ex. 3 Stoic habits for anxiety")
        with c2:
            vibe = st.selectbox("Style / Vibe", ["Fast Paced", "Cinematic Dark", "Luxury", "Tech", "Minimalist"])
        with c3:
            voice = st.selectbox("Voice", ["en-US-ChristopherNeural", "it-IT-DiegoNeural", "en-GB-SoniaNeural"])
        
        submitted = st.form_submit_button("🚀 START PRODUCTION")

    # --- LOGICA ESECUZIONE ---
    if submitted:
        if not user_api_key:
            st.error("❌ Errore: Manca la Gemini API Key (vedi sidebar).")
            return

        status = st.status("🏗️ Inizializzazione Workflow...", expanded=True)
        
        # 1. AI SCRIPT
        status.write("🧠 Gemini: Writing Script & Prompting...")
        scenes = generate_script(topic, vibe, user_api_key)
        
        if not scenes:
            status.update(label="❌ Errore AI. Riprova.", state="error")
            return

        # 2. RICERCA ASSET
        status.write("🎥 Hybrid Search: Hunting videos (Pexels -> Pixabay)...")
        final_scenes = []
        full_script_text = ""
        
        for scene in scenes:
            full_script_text += f"{scene['voiceover']} " # Accumula testo per TTS unico (opzionale)
            
            # Cerca video
            vid_data = get_hybrid_video(scene['keyword'], vibe)
            if vid_data:
                scene['video_link'] = vid_data['download']
                scene['preview'] = vid_data['preview']
                scene['source'] = vid_data['source']
            else:
                scene['video_link'] = None
                scene['source'] = "Not Found"
            
            final_scenes.append(scene)

        # 3. AUDIO ENGINE
        status.write("🎙️ Audio: Generating Neural Voiceover...")
        # Genera un unico file audio narrante per tutto il video
        voiceover_path = generate_voiceover_file(full_script_text, voice)
        
        status.write("🎵 Music: Finding best match on Pixabay...")
        music_page, music_dl = get_background_music(vibe)

        status.update(label="✅ Produzione Completata!", state="complete")

        # --- OUTPUT DISPLAY ---
        col_view, col_action = st.columns([2, 1])
        
        with col_view:
            st.subheader("Storyboard Preview")
            for s in final_scenes:
                with st.expander(f"Scene {s['scene_number']}: {s['keyword']} ({s['source']})"):
                    c_vid, c_txt = st.columns([1, 2])
                    with c_vid:
                        if s.get('preview'): st.image(s['preview'])
                    with c_txt:
                        st.write(f"**Voice:** {s['voiceover']}")
                        st.caption(f"Durata: {s['duration']}s")

        with col_action:
            st.subheader("📦 Final Export")
            st.success("Tutti gli asset sono pronti.")
            
            # Creazione ZIP
            zip_bytes = create_smart_package(final_scenes, music_dl, voiceover_path)
            
            st.download_button(
                label="⬇️ DOWNLOAD SMART PACK (.zip)",
                data=zip_bytes,
                file_name=f"TubeFlow_{topic.replace(' ','_')}.zip",
                mime="application/zip",
                type="primary"
            )
            st.info("Include: XML per DaVinci, file ordinati per CapCut, Voiceover e Musica.")

if __name__ == "__main__":
    main()