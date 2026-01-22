import streamlit as st
from dotenv import load_dotenv
import os
from modules.ai_engine import generate_script
from modules.asset_manager import get_pexels_video
from modules.utils import check_rate_limit, footer_legal

# Carica variabili d'ambiente
load_dotenv()

# --- PAGE CONFIGURATION (Wide layout for dashboard feel) ---
st.set_page_config(
    page_title="TubeFlow AI | 2026 Edition",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS INJECTION (2026 DESIGN SYSTEM) ---
st.markdown("""
    <style>
    /* RESET & BACKGROUND */
    .stApp {
        background-color: #050505;
        background-image: radial-gradient(circle at 50% 0%, #1a1a2e 0%, #050505 60%);
    }

    /* HERO SECTION */
    .hero-container {
        text-align: center;
        margin-bottom: 3rem;
        padding-top: 2rem;
    }
    .hero-title {
        font-family: 'Inter', sans-serif;
        font-size: 3.5rem;
        font-weight: 800;
        background: -webkit-linear-gradient(0deg, #00f2ea, #ff0050);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
    }
    .hero-subtitle {
        font-family: 'Inter', sans-serif;
        color: #e0e0e0;
        font-size: 1.2rem;
        font-weight: 300;
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }
    
    /* BADGES */
    .format-badge {
        display: inline-block;
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: #00f2ea;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        font-family: monospace;
        letter-spacing: 1px;
        margin: 5px;
    }

    /* INPUT FORM (GLASSMORPHISM) */
    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 2.5rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur( 4px );
        -webkit-backdrop-filter: blur( 4px );
    }

    /* INPUT FIELDS STYLING */
    .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #0a0a0a !important;
        color: white !important;
        border: 1px solid #333 !important;
        border-radius: 12px !important;
    }
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #0a0a0a !important;
        color: white !important;
    }
    
    /* NEON BUTTON */
    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%);
        color: #000;
        font-weight: 800;
        border: none;
        padding: 0.8rem 1rem;
        border-radius: 12px;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 15px;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 20px rgba(0, 201, 255, 0.5);
    }

    /* SCENE CARD STYLING */
    .scene-card {
        background: rgba(20, 20, 20, 0.6);
        border-left: 4px solid #00f2ea;
        border-radius: 0 16px 16px 0;
        padding: 20px;
        margin-bottom: 25px;
        border-top: 1px solid #222;
        border-right: 1px solid #222;
        border-bottom: 1px solid #222;
    }
    
    /* POPOVER MENU FIX */
    div[data-baseweb="popover"] {
        background-color: #111 !important;
        border: 1px solid #333;
    }
    
    /* CUSTOM LINKS */
    a.download-btn {
        display: inline-block;
        background-color: #222;
        color: #fff !important;
        padding: 8px 16px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: bold;
        border: 1px solid #444;
        margin-top: 10px;
        font-size: 0.8rem;
    }
    a.download-btn:hover {
        background-color: #fff;
        color: #000 !important;
        border-color: #fff;
    }
    
    /* HIDE STANDARD ELEMENTS */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

def main():
    # --- HERO SECTION (ENGLISH) ---
    st.markdown("""
        <div class="hero-container">
            <div class="hero-title">TUBEFLOW AI</div>
            <div class="hero-subtitle">
                Your Automated Video Director.<br>
                Turn ideas into production-ready plans with real stock footage.
            </div>
            <div class="format-badge">📱 FORMAT: 9:16 VERTICAL (SHORTS/TIKTOK)</div>
            <div class="format-badge">⚡ ASSETS: ROYALTY FREE (PEXELS)</div>
        </div>
    """, unsafe_allow_html=True)

    # --- INPUT AREA (GLASS CARD) ---
    with st.form("input_form"):
        # Layout [2, 1] per dare spazio al testo
        c1, c2 = st.columns([2, 1]) 
        
        with c1:
            st.markdown("**1. YOUR VIDEO IDEA**")
            topic = st.text_area("What is the video about?", placeholder="Ex. 5 habits to be more productive in the morning...", height=100, label_visibility="collapsed")
        
        with c2:
            st.markdown("**2. THE VIBE**")
            # Opzioni in Inglese per l'utenza internazionale
            vibe = st.selectbox("Select Style", ["Fast Paced (TikTok)", "Dark Documentary", "Luxury/Business", "Coding/Tech", "Calm/Minimalist"], label_visibility="collapsed")
            
        submitted = st.form_submit_button("⚡ GENERATE PLAN")

    # --- OUTPUT AREA ---
    if submitted and topic:
        check_rate_limit()
        
        # Status Bar in Inglese
        with st.status("🔮 AI Director is working...", expanded=True) as status:
            st.write("🧠 Gemini Flash Latest: Writing Script (Auto-Language Detect)...") 
            script_data = generate_script(topic, vibe)
            
            if not script_data:
                status.update(label="❌ System Failure. Please try again.", state="error")
                return
            
            st.write("📡 Pexels API: Finding best vertical videos...")
            final_plan = []
            
            for scene in script_data:
                keyword = scene.get('keyword', '')
                vid_prev, vid_link, author, author_url = get_pexels_video(keyword, vibe)
                
                scene['video_preview'] = vid_prev
                scene['video_link'] = vid_link
                scene['author'] = author
                scene['author_url'] = author_url
                final_plan.append(scene)
            
            status.update(label="✅ READY TO DEPLOY", state="complete")

        st.write("") # Spacer

        # --- CARDS VISUALIZZAZIONE ---
        st.markdown("### 📂 PROJECT FILES")
        
        for idx, scene in enumerate(final_plan):
            with st.container():
                c_text, c_vid = st.columns([0.55, 0.45])
                
                with c_text:
                    duration = scene.get('duration', 5)
                    st.markdown(f"""
                    <div class="scene-card">
                        <div style="color: #666; font-size: 0.8rem; margin-bottom: 5px;">SCENE {idx+1} • {duration}s</div>
                        <div style="font-size: 1.1rem; color: #fff; font-weight: 600; margin-bottom: 10px;">"{scene.get('voiceover')}"</div>
                        <div style="font-family: monospace; color: #00f2ea; background: rgba(0, 242, 234, 0.1); padding: 4px 8px; border-radius: 4px; display: inline-block;">
                            SEARCH QUERY: {scene.get('keyword')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with c_vid:
                    if scene.get('video_preview'):
                        st.video(scene['video_preview'])
                        
                        st.markdown(f"""
                            <div style="text-align: right; margin-top: -10px;">
                                <a href="{scene['video_link']}" target="_blank" class="download-btn">⬇ DOWNLOAD HD</a>
                                <div style="margin-top: 8px; font-size: 0.7rem; color: #555;">
                                    🎥 By <a href="{scene['author_url']}" style="color: #777; text-decoration: none;">{scene['author']}</a>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.warning("No footage found on Pexels.")
                
                st.write("---") 

    st.markdown("<div style='text-align: center; color: #333; margin-top: 50px; font-size: 0.8rem;'>TUBEFLOW v1.0 • POWERED BY GEMINI & PEXELS</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()