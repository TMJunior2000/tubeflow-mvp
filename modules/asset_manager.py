import requests
import streamlit as st
import os

def get_api_keys():
    pex = os.getenv("PEXELS_API_KEY") or st.secrets.get("PEXELS_API_KEY")
    pix = os.getenv("PIXABAY_API_KEY") or st.secrets.get("PIXABAY_API_KEY")
    return pex, pix

def validate_video_content(video_metadata, required_keyword):
    """
    Controlla se il video contiene davvero la parola chiave richiesta.
    """
    required = required_keyword.lower().strip()
    
    # Uniamo tutti i testi disponibili in una stringa di controllo
    # Pexels usa 'url', Pixabay usa 'tags'
    check_text = (
        video_metadata.get('url', '') + " " + 
        video_metadata.get('tags', '') + " " + 
        str(video_metadata.get('id', ''))
    ).lower()

    # Se la parola chiave principale non c'è, il video è SCARTATO.
    if required not in check_text:
        return False
    return True

def get_hybrid_video(keyword: str, orientation: str, excluded_urls=None):
    if excluded_urls is None: excluded_urls = []
    pex_key, pix_key = get_api_keys()
    
    # L'ancora è la prima parola (es. "Penguin" da "Penguin swimming")
    query = keyword.lower().strip()
    anchor_subject = query.split()[0] 
    
    candidates = []

    # 1. PEXELS SEARCH
    if pex_key:
        try:
            h = {"Authorization": pex_key}
            u = f"https://api.pexels.com/videos/search?query={query}&per_page=10&orientation={orientation}"
            r = requests.get(u, headers=h, timeout=5)
            if r.status_code == 200:
                for v in r.json().get("videos", []):
                    # VALIDAZIONE RIGIDA
                    if not validate_video_content(v, anchor_subject):
                        continue # Salta il video se non contiene l'ancora (es. Gallo)

                    link = None
                    for f in v['video_files']:
                        if f['quality'] == 'hd' and f['width'] >= 720: link = f['link']; break
                    if not link and v['video_files']: link = v['video_files'][0]['link']
                    
                    if link and link not in excluded_urls:
                        # Pexels score: alta risoluzione + match URL
                        candidates.append({"score": 10, "source": "Pexels", "preview": v['video_files'][0]['link'], "download": link})
        except: pass

    # 2. PIXABAY SEARCH
    if pix_key:
        try:
            p_orient = "vertical" if orientation == "portrait" else "horizontal"
            params = {"key": pix_key, "q": query, "per_page": 10, "orientation": p_orient, "video_type": "film"}
            r = requests.get("https://pixabay.com/api/videos/", params=params, timeout=5)
            if r.status_code == 200:
                for v in r.json().get('hits', []):
                    # VALIDAZIONE RIGIDA
                    if not validate_video_content(v, anchor_subject):
                        continue # Salta le meduse

                    score = 20 # Pixabay ha tag migliori, diamogli priorità se passa la validazione
                    link = v['videos'].get('medium', {}).get('url') or v['videos'].get('large', {}).get('url')
                    
                    if link and link not in excluded_urls:
                        candidates.append({"score": score, "source": "Pixabay", "preview": v['videos']['tiny']['url'], "download": link})
        except: pass

    # 3. SELEZIONE FINALE
    if not candidates: return None
    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates[0]