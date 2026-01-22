import requests
import streamlit as st
import os

def get_pexels_video(keyword: str):
    """
    Cerca un video verticale su Pexels e seleziona i file migliori per Preview e Download.
    """
    # 1. Recupero API Key
    api_key = os.getenv("PEXELS_API_KEY") or st.secrets.get("PEXELS_API_KEY")
    
    if not api_key:
        print("❌ Errore: PEXELS_API_KEY mancante.")
        return None, None, None, None

    # 2. Configurazione Header e URL (Docs: Authorization & Search)
    headers = {"Authorization": api_key}
    
    # Docs: "orientation=portrait" è supportato per i video
    url = f"https://api.pexels.com/videos/search?query={keyword}&per_page=1&orientation=portrait"
    
    try:
        r = requests.get(url, headers=headers, timeout=5)
        
        # Gestione Rate Limit (Opzionale per debug)
        # remaining = r.headers.get('X-Ratelimit-Remaining')
        
        if r.status_code == 200:
            data = r.json()
            if data.get("videos"):
                video = data["videos"][0]
                
                # --- A. Estrazione Dati Fotografo (Obbligatorio per Docs) ---
                photographer = video.get('user', {}).get('name', 'Pexels User')
                photographer_url = video.get('user', {}).get('url', 'https://www.pexels.com')
                
                # --- B. Logica di Selezione Qualità (Docs: Video Resource) ---
                files = video.get("video_files", [])
                
                preview_link = None
                download_link = None
                
                # Cerchiamo il file migliore
                for f in files:
                    # Per la PREVIEW: Cerchiamo un file 'sd' leggero (ma non piccolissimo)
                    if f.get('quality') == 'sd' and f.get('width', 0) < 1000:
                        preview_link = f['link']
                    
                    # Per il DOWNLOAD: Cerchiamo 'hd' (1080p o 720p)
                    # Preferiamo HD per la qualità finale
                    if f.get('quality') == 'hd':
                        download_link = f['link']
                
                # Fallback: Se non trova HD, prende l'SD. Se non trova SD, prende il primo disponibile.
                if not download_link and files:
                    download_link = files[0]['link']
                if not preview_link:
                    preview_link = download_link

                return preview_link, download_link, photographer, photographer_url
                
    except Exception as e:
        print(f"Errore Pexels: {e}")
        
    return None, None, None, None