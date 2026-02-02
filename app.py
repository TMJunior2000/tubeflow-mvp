import streamlit as st
import os

# Import Moduli
from modules.ai_engine import generate_script
from modules.asset_manager import get_hybrid_video, get_background_music
from modules.audio_engine import generate_voiceover_file
from modules.exporter import create_smart_package

st.set_page_config(page_title="TubeFlow AI", page_icon="⚡", layout="centered")

if 'credits' not in st.session_state:
    st.session_state['credits'] = 3

# --- CSS (Minimal & Dark) ---
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
    st.markdown('<div class="hero-title">TUBEFLOW AI</div>', unsafe_allow_html=True)
    
    credit_placeholder = st.empty()
    def show_credits():
        val = st.session_state['credits']
        credit_placeholder.markdown(f'<div class="credit-badge">⚡ CREDITS AVAILABLE: {val}</div>', unsafe_allow_html=True)
    show_credits()

    # --- INPUT FORM ---
    with st.form("creator_form"):
        st.markdown("**1. VIDEO CONCEPT**")
        # Placeholder educativo come discusso
        topic = st.text_area(
            "Di cosa parla il video?", 
            height=80, 
            placeholder="Esempio: Una giornata tipica di un pinguino in Antartide (Meglio di: 'Pinguino che salta')"
        )
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**2. STYLE**")
            vibe = st.selectbox("Vibe", ["Fast Paced", "Dark Cinematic", "Luxury", "Minimalist", "Nature Documentary"], label_visibility="collapsed")
        with c2:
            st.markdown("**3. FORMAT**")
            format_choice = st.radio("Ratio", ["9:16 (TikTok/Reels)", "16:9 (YouTube)"], label_visibility="collapsed")
            orientation = "portrait" if "9:16" in format_choice else "landscape"

        st.markdown("---")
        st.markdown("**4. AUDIO & LINGUA**")
        
        # --- FIX: LOGICA VOCE SEMPRE VISIBILE ---
        c3, c4 = st.columns(2)
        with c3:
            # Checkbox per attivare/disattivare
            use_voice = st.checkbox("🎙️ Generate Voiceover", value=True) 
            use_music = st.checkbox("🎵 Add Background Music", value=False)
            
        with c4:
            # Il menu DEVE essere visibile SUBITO per permetterti di scegliere ITA
            # Usiamo un dizionario per avere etichette belle ma ID tecnici
            voice_options = {
                "🇮🇹 Italiano (Diego)": "it-IT-DiegoNeural",
                "🇺🇸 English (Christopher)": "en-US-ChristopherNeural"
            }
            selected_label = st.selectbox("Lingua Voiceover", list(voice_options.keys()), label_visibility="collapsed")
            voice_id = voice_options[selected_label]

        # Disclaimer UI
        st.caption("ℹ️ *Se 'Generate Voiceover' non è spuntato, la lingua selezionata verrà ignorata.*")

        submit = st.form_submit_button("⚡ GENERATE PLAN")

    # --- LOGICA ---
    if submit:
        if not topic:
            st.warning("⚠️ Please enter a topic.")
            st.stop()
        if st.session_state['credits'] <= 0:
            st.error("❌ Out of credits!")
            st.stop()

        st.session_state['credits'] -= 1
        show_credits()

        with st.status("🔮 Magic in progress...", expanded=True) as status:
            st.write("🧠 Designing Script...")
            scenes = generate_script(topic, vibe)
            
            if not scenes:
                status.update(label="❌ AI Error.", state="error")
                st.session_state['credits'] += 1
                st.stop()

            st.write(f"🎥 Hunting Visuals ({orientation.upper()})...")
            final_scenes = []
            full_text = ""
            for s in scenes:
                full_text += s['voiceover'] + " "
                # Passiamo l'orientation al cercatore!
                vid = get_hybrid_video(s['keyword'], vibe, orientation)
                if vid:
                    s['video_link'] = vid['download']
                    s['preview'] = vid['preview']
                    s['source'] = vid['source']
                else:
                    s['video_link'] = None
                    s['source'] = "Not Found"
                final_scenes.append(s)

            music_url = None
            voice_path = None

            if use_music:
                st.write("🎵 Finding Music...")
                music_data = get_background_music(vibe)
                # IMPORTANTE: music_data è una tupla (page, mp3).
                # Non serve scompattarla qui se 'create_smart_package' la gestisce,
                # MA per sicurezza passiamo direttamente il link mp3.
                if music_data:
                     music_url = music_data[1]  # <--- Assicurati che sia così o passa 'music_data' intero

            if use_voice and voice_id:
                st.write("🎙️ Recording Voiceover...")
                voice_path = generate_voiceover_file(full_text, voice_id)

            st.write("📦 Packaging...")
            # Chiamata corretta
            zip_data = create_smart_package(final_scenes, orientation, music_url, voice_path)
            
            status.update(label="✅ GENERATION COMPLETE", state="complete")

        st.markdown("---")
        st.success(f"✅ Your {format_choice} project is ready!")

        for s in final_scenes:
            with st.expander(f"Scene {s['scene_number']}: {s['keyword']}"):
                col_img, col_info = st.columns([1, 2])
                with col_img:
                    preview_url = s.get('preview')
                    if preview_url:
                        if ".mp4" in preview_url or ".webm" in preview_url:
                            st.video(preview_url)
                        else:
                            st.image(preview_url, use_container_width=True)
                    else:
                        st.caption("No preview")
                with col_info:
                    st.caption(f"Source: {s.get('source', 'Unknown')}")
                    st.write(f"**Script:** {s['voiceover']}")

        st.download_button(
            label=f"⬇️ DOWNLOAD {format_choice} PACK",
            data=zip_data,
            file_name=f"TubeFlow_{orientation}.zip",
            mime="application/zip",
            type="primary"
        )

if __name__ == "__main__":
    main()