import requests
import streamlit as st
import os

def get_api_keys():
    pex = os.getenv("PEXELS_API_KEY") or st.secrets.get("PEXELS_API_KEY")
    pix = os.getenv("PIXABAY_API_KEY") or st.secrets.get("PIXABAY_API_KEY")
    return pex, pix

def get_hybrid_video(keyword: str, orientation: str, excluded_urls=None):
    if excluded_urls is None: excluded_urls = []
    pex_key, pix_key = get_api_keys()
    query = keyword.lower().strip()
    
    candidates = []

    # 1. RACCOLTA CANDIDATI DA PEXELS
    if pex_key:
        try:
            h = {"Authorization": pex_key}
            u = f"https://api.pexels.com/videos/search?query={query}&per_page=5&orientation={orientation}"
            r = requests.get(u, headers=h, timeout=5)
            if r.status_code == 200:
                for v in r.json().get("videos", []):
                    # Pexels non invia tag chiari via API per i video, usiamo l'alt o il titolo della URL
                    score = 0
                    if query in v.get('url', '').lower(): score += 5
                    
                    link = v['video_files'][0]['link']
                    for f in v['video_files']:
                        if f['quality'] == 'hd' and f['width'] >= 720: link = f['link']; break
                    
                    if link not in excluded_urls:
                        candidates.append({
                            "score": score,
                            "source": "Pexels",
                            "preview": v['video_files'][0]['link'],
                            "download": link
                        })
        except: pass

    # 2. RACCOLTA CANDIDATI DA PIXABAY
    if pix_key:
        try:
            p_orient = "vertical" if orientation == "portrait" else "horizontal"
            params = {"key": pix_key, "q": query, "per_page": 5, "orientation": p_orient, "video_type": "film"}
            r = requests.get("https://pixabay.com/api/videos/", params=params, timeout=5)
            if r.status_code == 200:
                for v in r.json().get('hits', []):
                    # Pixabay fornisce tag espliciti, molto utili per la coerenza
                    tags = v.get('tags', '').lower()
                    score = 0
                    for word in query.split():
                        if word in tags: score += 10 # Punteggio alto se la parola è nei tag
                    
                    link = v['videos'].get('medium', {}).get('url') or v['videos'].get('large', {}).get('url')
                    if link and link not in excluded_urls:
                        candidates.append({
                            "score": score,
                            "source": "Pixabay",
                            "preview": v['videos']['tiny']['url'],
                            "download": link
                        })
        except: pass

    # 3. SELEZIONE DELLA CLIP MIGLIORE
    if not candidates: return None
    
    # Ordiniamo per punteggio (il più alto vince)
    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates[0]