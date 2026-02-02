import streamlit as st
import os

# Import Moduli
from modules.ai_engine import generate_script
from modules.asset_manager import get_hybrid_video, get_background_music
from modules.audio_engine import generate_voiceover_file
from modules.exporter import create_smart_package

# Configurazione Pagina
st.set_page_config(page_title="TubeFlow AI", page_icon="⚡", layout="centered")

# --- GESTIONE CREDITI (SESSION STATE) ---
if 'credits' not in st.session_state:
    st.session_state['credits'] = 3 # Start gratuito

# --- CSS STYLES ---
st.markdown("""
    <style>
    .stApp {
        background-color: #050505;
        background-image: radial-gradient(circle at 50% 0%, #1a1a2e 0%, #050505 60%);
    }
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
    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 2rem;
        backdrop-filter: blur(10px);
    }
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
    </style>
""", unsafe_allow_html=True)

def main():
    # --- HERO SECTION ---
    st.markdown('<div class="hero-title">TUBEFLOW AI</div>', unsafe_allow_html=True)
    
    # 1. PLACEHOLDER PER I CREDITI (Così possiamo aggiornarlo senza rerun)
    credit_placeholder = st.empty()
    
    # Funzione per renderizzare il badge
    def show_credits():
        val = st.session_state['credits']
        credit_placeholder.markdown(f'<div class="credit-badge">⚡ CREDITS AVAILABLE: {val}</div>', unsafe_allow_html=True)
    
    show_credits() # Mostra stato iniziale

    # --- INPUT FORM ---
    with st.form("creator_form"):
        st.markdown("**1. VIDEO CONCEPT**")
        topic = st.text_area("What is the video about?", height=80, placeholder="Ex. 3 tips for better sleep...")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**2. STYLE**")
            vibe = st.selectbox("Vibe", ["Fast Paced", "Dark Cinematic", "Luxury", "Minimalist"], label_visibility="collapsed")
        with c2:
            st.markdown("**3. ADD-ONS (Optional)**")
            use_voice = st.checkbox("Generate Voiceover", value=False)
            use_music = st.checkbox("Add Background Music", value=False)
            
            if use_voice:
                voice_id = st.selectbox("Voice", ["en-US-ChristopherNeural", "it-IT-DiegoNeural"], label_visibility="collapsed")
            else:
                voice_id = None

        submit = st.form_submit_button("⚡ GENERATE PLAN")

    # --- LOGICA DI GENERAZIONE ---
    if submit:
        # VALIDAZIONI
        if not topic:
            st.warning("⚠️ Please enter a topic.")
            st.stop()

        if st.session_state['credits'] <= 0:
            st.error("❌ Out of credits! Please upgrade to Pro.")
            st.stop()

        # DEDUZIONE CREDITO E UPDATE UI IMMEDIATO
        st.session_state['credits'] -= 1
        show_credits() # Aggiorna il numero visivamente ORA

        # ESECUZIONE WORKFLOW
        with st.status("🔮 Magic in progress...", expanded=True) as status:
            
            # 1. AI Script
            st.write("🧠 Designing Script...")
            scenes = generate_script(topic, vibe)
            
            if not scenes:
                status.update(label="❌ AI Error. Credits refunded.", state="error")
                st.session_state['credits'] += 1 # Rimborso se fallisce
                st.stop()

            # 2. Asset Hunt
            st.write("🎥 Hunting Visuals (Pexels/Pixabay)...")
            final_scenes = []
            full_text = ""
            for s in scenes:
                full_text += s['voiceover'] + " "
                vid = get_hybrid_video(s['keyword'], vibe)
                if vid:
                    s['video_link'] = vid['download']
                    s['preview'] = vid['preview']
                    s['source'] = vid['source']
                else:
                    s['video_link'] = None
                    s['source'] = "Not Found"
                final_scenes.append(s)

            # 3. Optionals
            music_url = None
            voice_path = None

            if use_music:
                st.write("🎵 Finding Music...")
                _, music_url = get_background_music(vibe)
            
            if use_voice and voice_id:
                st.write("🎙️ Recording Voiceover...")
                voice_path = generate_voiceover_file(full_text, voice_id)

            st.write("📦 Packaging...")
            zip_data = create_smart_package(final_scenes, music_url, voice_path)
            
            status.update(label="✅ GENERATION COMPLETE", state="complete")

        # --- OUTPUT DISPLAY ---
        st.markdown("---")
        st.success("✅ Your project is ready!")

        # Anteprima Scene
        for s in final_scenes:
            with st.expander(f"Scene {s['scene_number']}: {s['keyword']}"):
                col_img, col_info = st.columns([1, 2])
                with col_img:
                    if s.get('preview'):
                        st.image(s['preview'])
                    else:
                        st.caption("No preview")
                with col_info:
                    st.caption(f"Source: {s.get('source')}")
                    st.write(f"**Script:** {s['voiceover']}")

        # Bottone Download
        st.download_button(
            label=f"⬇️ DOWNLOAD PACK ({len(zip_data)/1024/1024:.1f} MB)",
            data=zip_data,
            file_name="TubeFlow_Pack.zip",
            mime="application/zip",
            type="primary"
        )

if __name__ == "__main__":
    main()