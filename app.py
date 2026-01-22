import streamlit as st
from modules.ai_engine import generate_script
from modules.asset_manager import get_pexels_video
from modules.utils import check_rate_limit, footer_legal
from dotenv import load_dotenv

load_dotenv()


# Configurazione Pagina
st.set_page_config(page_title="TubeFlow | AI Video Planner", page_icon="🎬", layout="centered")

# CSS Custom
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stButton>button {width: 100%; border-radius: 8px; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.title("🎬 TubeFlow Orchestrator")
    st.caption("Dall'idea al piano di montaggio (con asset gratis) in 30 secondi.")
    st.info("💡 **Come funziona:** Tu scrivi l'idea, l'AI scrive lo script e trova i video stock gratuiti da Pexels pronti per DaVinci/CapCut.")

    # Input Area
    with st.form("input_form"):
        topic = st.text_area("Di cosa parla il tuo video?", placeholder="Es. 3 consigli per studiare meglio, stile veloce...")
        vibe = st.selectbox("Stile Video", ["TikTok Veloce", "Tutorial Calmo", "Motivazionale", "Cinematico"])
        submitted = st.form_submit_button("🚀 Genera Piano Regia")

    # Output Area
    if submitted and topic:
        check_rate_limit()
        
        with st.status("🤖 L'AI sta lavorando...", expanded=True) as status:
            st.write("📝 Scrittura sceneggiatura strutturata...")
            
            script_data = generate_script(topic, vibe)
            
            if not script_data:
                status.update(label="❌ Errore generazione.", state="error")
                return
            
            st.write("🔍 Ricerca asset su Pexels...")
            final_plan = []
            
            for scene in script_data:
                # Recupero dati sicuro
                keyword = scene.get('keyword', '')
                vid_prev, vid_link, author, author_url = get_pexels_video(keyword)
                
                scene['video_preview'] = vid_prev
                scene['video_link'] = vid_link
                scene['author'] = author
                scene['author_url'] = author_url
                final_plan.append(scene)
            
            status.update(label="✅ Piano completato!", state="complete")

        # Visualizzazione Risultati
        st.divider()
        st.subheader("Il tuo Piano di Produzione")
        
        for idx, scene in enumerate(final_plan):
            with st.container():
                c1, c2 = st.columns([0.6, 0.4])
                
                with c1:
                    duration = scene.get('duration', 5)
                    st.markdown(f"**SCENA {idx+1}** ({duration}s)")
                    st.success(f"🗣️ **Voiceover:** \"{scene.get('voiceover')}\"")
                    st.caption(f"Keyword usata: `{scene.get('keyword')}`")
                
                with c2:
                    if scene.get('video_preview'):
                        st.video(scene['video_preview'])
                        st.markdown(f"👉 [**Scarica Asset (Pexels)**]({scene['video_link']})")
                    
                        if scene.get('author'):
                            st.caption(f"🎥 Video by [{scene['author']}]({scene['author_url']}) on Pexels")
                        else:
                            st.warning(f"Nessun video trovato per: {scene.get('keyword')}")
                    
                    else:
                        st.warning(f"Nessun video trovato per: {scene.get('keyword')}")
                
                st.divider()
        
        st.success("Ti è stato utile? Fammi sapere nei commenti su Reddit! 👋")

    footer_legal()

if __name__ == "__main__":
    main()