import requests
import streamlit as st
import random
import os

def get_api_keys():
    """Recupera chiavi dai secrets di Streamlit."""
    pex = os.getenv("PEXELS_API_KEY") or st.secrets.get("PEXELS_API_KEY")
    pix = os.getenv("PEXELS_API_KEY") or st.secrets.get("PIXABAY_API_KEY")
    return pex, pix

def get_hybrid_video(keyword: str, vibe: str):
    """
    Logica Waterfall: Pexels (Qualità) -> Fallback Pixabay (Quantità).
    """
    pex_key, pix_key = get_api_keys()
    
    # 1. Tentativo Pexels (Priorità al Verticale)
    if pex_key:
        video = _search_pexels(keyword, vibe, pex_key)
        if video: return video | {"source": "Pexels"}
    
    # 2. Tentativo Pixabay (Fallback)
    if pix_key:
        video = _search_pixabay(keyword, vibe, pix_key)
        if video: return video | {"source": "Pixabay"}

    return None

def _search_pexels(keyword, vibe, key):
    headers = {"Authorization": key}
    # Logica colori per vibe
    color = "&color=000000" if "Dark" in vibe else ""
    url = f"https://api.pexels.com/videos/search?query={keyword}&per_page=1&orientation=portrait{color}"
    
    try:
        r = requests.get(url, headers=headers, timeout=5)
        data = r.json()
        if data.get("videos"):
            vid = data["videos"][0]
            # Cerca link HD
            dl_link = next((f['link'] for f in vid['video_files'] if f['quality']=='hd'), vid['video_files'][0]['link'])
            return {
                "preview": vid['video_files'][0]['link'],
                "download": dl_link,
                "author": vid['user']['name']
            }
    except Exception:
        pass
    return None

def _search_pixabay(keyword, vibe, key):
    # Aggiungiamo 'vertical' alla query perché il filtro API a volte fallisce
    query = keyword
    url = f"https://pixabay.com/api/videos/?key={key}&q={query}&video_type=film&per_page=3"
    
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        if int(data.get("totalHits", 0)) > 0:
            vid = data["hits"][0]
            # Pixabay struttura diversa
            return {
                "preview": vid["videos"]["tiny"]["url"],
                "download": vid["videos"]["medium"]["url"],
                "author": f"PixabayUser_{vid['user_id']}"
            }
    except Exception:
        pass
    return None

def get_background_music(vibe: str):
    """Scarica musica MP3 da Pixabay Audio."""
    _, pix_key = get_api_keys()
    if not pix_key: return None, None
    
    # Mapping Vibe -> Tag Musicale
    tag = "ambient"
    if "Fast Paced" in vibe: tag = "upbeat"
    elif "Dark" in vibe: tag = "cinematic"
    elif "Tech" in vibe: tag = "electronic"
    
    url = f"https://pixabay.com/api/?key={pix_key}&q={tag}&category=music&per_page=3"
    
    try:
        r = requests.get(url, timeout=3)
        data = r.json()
        if int(data.get("totalHits", 0)) > 0:
            track = random.choice(data["hits"])
            return track["pageURL"], track["videos"]["large"]["url"] # URL MP3
    except:
        pass
    return None, None