import requests
import streamlit as st
import random
import os

def get_api_keys():
    pex = os.getenv("PEXELS_API_KEY") or st.secrets.get("PEXELS_API_KEY")
    pix = os.getenv("PIXABAY_API_KEY") or st.secrets.get("PIXABAY_API_KEY")
    return pex, pix

def get_hybrid_video(keyword: str, orientation: str, excluded_urls=None):
    if excluded_urls is None: excluded_urls = []
    pex_key, pix_key = get_api_keys()
    
    # Pulizia e preparazione query
    query = keyword.strip()
    
    # 1. TENTATIVO PEXELS (Priorità Qualità)
    if pex_key:
        try:
            h = {"Authorization": pex_key}
            u = f"https://api.pexels.com/videos/search?query={query}&per_page=10&orientation={orientation}"
            r = requests.get(u, headers=h, timeout=5)
            if r.status_code == 200:
                videos = r.json().get("videos", [])
                random.shuffle(videos)
                for v in videos:
                    link = v['video_files'][0]['link']
                    # Scegli HD se disponibile
                    for f in v['video_files']:
                        if f['quality'] == 'hd' and f['width'] >= 720: 
                            link = f['link']; break
                    if link not in excluded_urls:
                        return {"source": "Pexels", "preview": v['video_files'][0]['link'], "download": link}
        except: pass

    # 2. TENTATIVO PIXABAY (Fallback)
    if pix_key:
        try:
            p_orient = "vertical" if orientation == "portrait" else "horizontal"
            params = {"key": pix_key, "q": query, "per_page": 10, "orientation": p_orient}
            r = requests.get("https://pixabay.com/api/videos/", params=params, timeout=5)
            if r.status_code == 200:
                hits = r.json().get('hits', [])
                random.shuffle(hits)
                for v in hits:
                    link = v['videos']['medium']['url'] or v['videos']['small']['url']
                    if link not in excluded_urls:
                        return {"source": "Pixabay", "preview": v['videos']['tiny']['url'], "download": link}
        except: pass
    
    return None