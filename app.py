import streamlit as st
from modules.ai_engine import generate_script
from modules.asset_manager import get_hybrid_video
from modules.audio_engine import generate_voiceover_file
from modules.exporter import create_smart_package
from modules.utils import footer_legal

st.set_page_config(page_title="TubeFlow AI", page_icon="⚡", layout="centered")

if 'generated_content' not in st.session_state: st.session_state['generated_content'] = None

st.markdown("""
    <style>
    .stApp { background-color: #050505; background-image: radial-gradient(circle at 50% 0%, #1a1a2e 0%, #050505 60%); color: #fff; }
    .hero-title { font-family: 'Inter', sans-serif; font-size: 3rem; font-weight: 800; background: -webkit-linear-gradient(0deg, #00f2ea, #ff0050); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    div[data-testid="stForm"] { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 24px; padding: 2rem; backdrop-filter: blur(10px); }
    .stButton > button { background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%); color: #000; font-weight: bold; border: none; border-radius: 12px; height: 50px; font-size: 1.1rem; width: 100%; }
    </style>
""", unsafe_allow_html=True)

def main():
    st.markdown('<div class="hero-title">TUBEFLOW AI</div>', unsafe_allow_html=True)
    # RIMOSSO BADGE CREDITI

    with st.form("creator_form"):
        topic = st.text_area("VIDEO CONCEPT", height=80, placeholder="Es. Samurai sotto la pioggia...")
        c1, c2 = st.columns(2)
        with c1:
            format_choice = st.radio("Format", ["9:16 (Reels)", "16:9 (YouTube)"], label_visibility="collapsed")
            orientation = "portrait" if "9:16" in format_choice else "landscape"
        with c2:
            voice_choice = st.selectbox("Language", ["🇮🇹 Italiano (Diego)", "🇺🇸 English (Christopher)"], label_visibility="collapsed")
            voice_id = "it-IT-DiegoNeural" if "Italiano" in voice_choice else "en-US-ChristopherNeural"
        
        use_voice = st.checkbox("🎙️ Generate Voiceover", True) 
        
        submit = st.form_submit_button("⚡ GENERATE MAGIC")

    if submit:
        # RIMOSSO CHECK CREDITI E RATE LIMIT
        if not topic: st.warning("Topic Missing!"); st.stop()
        
        st.session_state['generated_content'] = None

        with st.status("🔮 AI Director is working...", expanded=True) as status:
            
            # 1. AI SCRIPT (Con Auto-Retry integrato)
            st.write("🧠 AI Scripting...")
            script_data = generate_script(topic)
            
            if not script_data: 
                status.update(label="❌ AI Error", state="error")
                st.stop()
            
            scenes = script_data['scenes']
            voice_settings = script_data['voice_settings'] 
            voice_speed = voice_settings['voice_speed']
            
            st.info(f"Voice Speed: {voice_speed} | Scenes: {len(scenes)}")

            # 2. VIDEO HUNTING
            st.write("🎥 Hunting Visuals (Pexels/Pixabay)...")
            final_scenes = []
            full_text = ""
            for s in scenes:
                full_text += s['voiceover'] + " "
                vid = get_hybrid_video(s['keyword'], "", orientation)
                if vid: 
                    s.update(vid)
                    s['video_link'] = vid['download']
                else:
                    s['video_link'] = None 
                final_scenes.append(s)

            # 3. VOICE
            voice_path = None
            if use_voice:
                st.write("🎙️ Recording Voice...")
                voice_path = generate_voiceover_file(full_text, voice_id, voice_speed)

            # 4. PACKAGING
            st.write("📦 Packaging...")
            zip_data = create_smart_package(final_scenes, orientation, music_data_tuple=None, voiceover_path=voice_path)
            
            st.session_state['generated_content'] = {
                "scenes": final_scenes, 
                "zip_data": zip_data, 
                "file_name": f"TubeFlow_{orientation}.zip"
            }
            status.update(label="✅ COMPLETE", state="complete")

    if st.session_state['generated_content']:
        content = st.session_state['generated_content']
        st.success("Project Ready! (Add Trending Audio inside TikTok/Reels)")
        
        for s in content['scenes']:
            with st.expander(f"Scene {s['scene_number']}: {s['keyword']} [{s.get('source', '?')}]"):
                if s.get('preview'): st.video(s['preview'])
                st.write(s['voiceover'])
        
        st.download_button("⬇️ DOWNLOAD ZIP", content['zip_data'], content['file_name'], "application/zip", type="primary")

    footer_legal()

if __name__ == "__main__":
    main()