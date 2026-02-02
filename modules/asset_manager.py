import requests
import streamlit as st
import random
import os

def get_api_keys():
    pex = os.getenv("PEXELS_API_KEY") or st.secrets.get("PEXELS_API_KEY")
    pix = os.getenv("PIXABAY_API_KEY") or st.secrets.get("PIXABAY_API_KEY")
    return pex, pix

# --- HEADERS PER RICERCA API (Solo User-Agent, NO Referer) ---
def get_search_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }

# ==========================================
# 🎥 SEZIONE VIDEO (Best Match Wins)
# ==========================================
def get_hybrid_video(keyword: str, vibe: str, orientation: str):
    pex_key, pix_key = get_api_keys()
    
    base_keyword = keyword.replace("Vertical", "").replace("Portrait", "").replace("Landscape", "").strip()
    words = base_keyword.split()
    
    breadcrumbs = []
    for i in range(len(words), 0, -1):
        breadcrumbs.append(" ".join(words[:i]))
    if not breadcrumbs: breadcrumbs = [base_keyword]

    print(f"🔍 Search Strategy: {breadcrumbs}")

    for attempt, query in enumerate(breadcrumbs):
        match_label = "🟢 EXACT MATCH" if attempt == 0 else "🟡 BROAD MATCH"

        # Pexels
        vid_pex = None
        if pex_key:
            vid_pex = _search_pexels(query, orientation, pex_key)

        # Pixabay
        vid_pix = None
        if pix_key:
            vid_pix = _search_pixabay(query, orientation, pix_key)

        # ARBITRAGGIO
        if vid_pex and vid_pix:
            return vid_pex | {'match_type': match_label} # Pexels vince per qualità
        if vid_pex:
            return vid_pex | {'match_type': match_label}
        if vid_pix:
            return vid_pix | {'match_type': match_label}
    
    return None

def _search_pexels(keyword, orientation, key):
    try:
        h = {"Authorization": key}
        u = f"https://api.pexels.com/videos/search?query={keyword}&per_page=1&orientation={orientation}"
        r = requests.get(u, headers=h, timeout=5)
        if r.status_code == 200:
            d = r.json()
            if d.get("videos"):
                v = d["videos"][0]
                dl = v['video_files'][0]['link']
                for f in v['video_files']:
                    if f['quality'] == 'hd' and f['width'] >= 720: 
                        dl = f['link']; break
                return {"source":"Pexels", "preview": v['video_files'][0]['link'], "download": dl}
    except: pass
    return None

def _search_pixabay(keyword, orientation, key):
    try:
        pix_query = f"{keyword} vertical" if orientation == "portrait" else keyword
        params = {"key": key, "q": pix_query, "per_page": 3}
        u = "https://pixabay.com/api/videos/"
        r = requests.get(u, params=params, timeout=5)
        if r.status_code == 200:
            d = r.json()
            if int(d.get('totalHits', 0)) > 0:
                v = d['hits'][0]
                dl = v['videos']['tiny']['url']
                if 'medium' in v['videos'] and v['videos']['medium']['size'] > 0: 
                    dl = v['videos']['medium']['url']
                elif 'small' in v['videos']: 
                    dl = v['videos']['small']['url']
                return {"source":"Pixabay", "preview": v['videos']['tiny']['url'], "download": dl}
    except: pass
    return None

# ==========================================
# 🎵 SEZIONE AUDIO (API Ufficiale)
# ==========================================
def get_pixabay_audio(genre: str, mood: str):
    _, pix_key = get_api_keys()
    if not pix_key: return None, "ERRORE: API Key mancante."

    url = "https://pixabay.com/api/audio/"
    params = {"key": pix_key, "q": f"{genre} {mood}", "per_page": 10, "category": "music"}
    
    try:
        r = requests.get(url, params=params, headers=get_search_headers(), timeout=10)
        if r.status_code != 200: return None, f"HTTP ERROR {r.status_code}"

        data = r.json()
        hits = data.get("hits", [])
        
        if len(hits) == 0:
            params["q"] = mood # Retry
            r2 = requests.get(url, params=params, headers=get_search_headers(), timeout=10)
            if r2.status_code == 200 and r2.json().get("hits"):
                track = random.choice(r2.json()["hits"])
                return track.get("pageURL"), track.get("url")
            else:
                return None, f"NESSUN RISULTATO"

        track = random.choice(hits)
        # Ritorna TUPLA: (LinkPagina, LinkMp3)
        return track.get("pageURL"), track.get("url")

    except Exception as e:
        return None, f"EXCEPTION: {str(e)}"