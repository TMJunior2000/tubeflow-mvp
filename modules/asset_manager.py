import requests
import streamlit as st
import random
import os

def get_api_keys():
    pex = os.getenv("PEXELS_API_KEY") or st.secrets.get("PEXELS_API_KEY")
    pix = os.getenv("PIXABAY_API_KEY") or st.secrets.get("PIXABAY_API_KEY")
    return pex, pix

# --- VIDEO SEARCH (Resta uguale, è perfetto) ---
def get_hybrid_video(keyword: str, vibe: str, orientation: str): # Vibe ignorato qui, usiamo keyword
    pex_key, pix_key = get_api_keys()
    base_keyword = keyword.replace("Vertical", "").replace("Portrait", "").replace("Landscape", "").strip()
    
    words = base_keyword.split()
    breadcrumbs = []
    for i in range(len(words), 0, -1):
        breadcrumbs.append(" ".join(words[:i]))
    if not breadcrumbs: breadcrumbs = [base_keyword]

    print(f"🔍 Searching: {breadcrumbs}")

    for attempt, query in enumerate(breadcrumbs):
        is_last = (attempt == len(breadcrumbs) - 1) and len(breadcrumbs) > 1
        match_label = "🟢 EXACT MATCH" if attempt == 0 else "🟠 SUBJECT ONLY" if is_last else "🟡 BROAD MATCH"

        vid_pex = _search_pexels(query, orientation, pex_key) if pex_key else None
        vid_pix = _search_pixabay(query, orientation, pix_key) if pix_key else None

        if vid_pex and vid_pix:
            winner = random.choice([vid_pex, vid_pix])
            return winner | {'match_type': match_label}
        if vid_pex: return vid_pex | {'match_type': match_label}
        if vid_pix: return vid_pix | {'match_type': match_label}
    
    return None

def _search_pexels(keyword, orientation, key):
    headers = {"Authorization": key}
    url = f"https://api.pexels.com/videos/search?query={keyword}&per_page=1&orientation={orientation}"
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("videos"):
                v = data["videos"][0]
                dl = v['video_files'][0]['link']
                for f in v['video_files']:
                    if f['quality'] == 'hd' and f['width'] >= 720:
                        dl = f['link']; break
                return {"source":"Pexels", "preview": v['video_files'][0]['link'], "download": dl}
    except: pass
    return None

def _search_pixabay(keyword, orientation, key):
    suffix = " vertical" if orientation == "portrait" else ""
    url = f"https://pixabay.com/api/videos/?key={key}&q={keyword}{suffix}&per_page=3"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200 and int(r.json().get('totalHits', 0)) > 0:
            v = r.json()['hits'][0]
            dl = v['videos']['medium']['url'] or v['videos']['small']['url']
            return {"source":"Pixabay", "preview": v['videos']['tiny']['url'], "download": dl}
    except: pass
    return None

# --- AUDIO SEARCH (API REALE) ---
def get_contextual_music(query: str):
    """
    Cerca musica su Pixabay usando l'endpoint AUDIO corretto.
    Usa la query generata dall'AI (es. 'Sad', 'Epic').
    """
    _, pix_key = get_api_keys()
    if not pix_key: return None, None

    # Endpoint specifico AUDIO (diverso da immagini/video)
    url = f"https://pixabay.com/api/audio/?key={pix_key}&q={query}&per_page=3"
    
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if int(data.get("totalHits", 0)) > 0:
                track = random.choice(data["hits"])
                # Pixabay Audio Object: 'url' è il link all'mp3
                # 'pageURL' è la pagina dei credits
                mp3_link = track.get("url") 
                page_link = track.get("pageURL")
                
                print(f"🎵 Found Music: {query} -> {mp3_link}")
                return page_link, mp3_link
    except Exception as e:
        print(f"Audio API Error: {e}")
    
    return None, None