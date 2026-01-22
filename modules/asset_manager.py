import requests
import streamlit as st
import os

def get_pexels_video(keyword: str, vibe: str = "General"): # <--- Aggiunto parametro vibe
    """
    Cerca video su Pexels filtrando per Colore/Stile per garantire coerenza visiva.
    """
    api_key = os.getenv("PEXELS_API_KEY") or st.secrets.get("PEXELS_API_KEY")
    
    if not api_key:
        print("❌ Errore: PEXELS_API_KEY mancante.")
        return None, None, None, None

    headers = {"Authorization": api_key}
    
    # --- LOGICA "VISUAL GLUE" (Coerenza Cromatica) ---
    # Mappiamo le Vibes a codici colore HEX o keyword stilistiche
    color_param = ""
    style_suffix = ""
    
    if "Dark" in vibe:
        color_param = "&color=000000" # Cerca video scuri/neri
        style_suffix = " dark moody"
    elif "Luxury" in vibe:
        color_param = "&color=DAA520" # Golden Rod (Toni Oro/Marrone)
        style_suffix = " luxury elegant"
    elif "Tech" in vibe:
        color_param = "&color=0000FF" # Toni Blu/Freddi
        style_suffix = " futuristic blue"
    elif "Minimalist" in vibe:
        color_param = "&color=E6E6FA" # Lavender/White (Toni chiari)
        style_suffix = " bright clean"
    else:
        # Per "Fast Paced" o generici, non filtriamo il colore ma cerchiamo qualità
        color_param = "" 
        style_suffix = ""

    # Costruiamo la query arricchita (Keyword + Stile)
    final_query = f"{keyword}{style_suffix}"
    
    # URL con parametro COLOR e orientamento
    url = f"https://api.pexels.com/videos/search?query={final_query}&per_page=1&orientation=portrait{color_param}"
    
    try:
        r = requests.get(url, headers=headers, timeout=5)
        
        if r.status_code == 200:
            data = r.json()
            if data.get("videos"):
                video = data["videos"][0]
                
                photographer = video.get('user', {}).get('name', 'Pexels User')
                photographer_url = video.get('user', {}).get('url', 'https://www.pexels.com')
                
                files = video.get("video_files", [])
                preview_link = None
                download_link = None
                
                for f in files:
                    if f.get('quality') == 'sd' and f.get('width', 0) < 1000:
                        preview_link = f['link']
                    if f.get('quality') == 'hd':
                        download_link = f['link']
                
                if not download_link and files:
                    download_link = files[0]['link']
                if not preview_link:
                    preview_link = download_link

                return preview_link, download_link, photographer, photographer_url
                
    except Exception as e:
        print(f"Errore Pexels: {e}")
        
    return None, None, None, None