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
    Cerca musica su Pixabay con strategia 'Search & Rescue'.
    1. Prova la query specifica.
    2. Se 0 risultati, prova la query generica (solo la prima parola).
    3. Se fallisce tutto, usa un MP3 di backup garantito.
    """
    _, pix_key = get_api_keys()
    
    # Lista di backup (Link diretti CDN stabili)
    SAFE_FALLBACK_MP3 = "https://cdn.pixabay.com/download/audio/2022/03/24/audio_1969a58943.mp3" # Brano 'Cinematic' generico
    
    if not pix_key: 
        print("⚠️ Pixabay Key mancante. Uso Fallback.")
        return "Generic Music", SAFE_FALLBACK_MP3

    # Tentativi di ricerca
    search_attempts = [
        query,                  # Es: "Epic Japanese Drums" (Specifico)
        query.split()[0],       # Es: "Epic" (Generico)
        "Cinematic"             # Es: "Cinematic" (Sicuro)
    ]

    for q in search_attempts:
        if len(q) < 3: continue # Salta query troppo corte
        
        url = f"https://pixabay.com/api/audio/?key={pix_key}&q={q}&per_page=3"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                if int(data.get("totalHits", 0)) > 0:
                    track = random.choice(data["hits"])
                    # Pixabay a volte chiama il campo 'url', a volte è nascosto.
                    # Ma 'url' è lo standard per l'audio preview (che è un mp3 completo).
                    mp3_link = track.get("url") 
                    if mp3_link:
                        print(f"🎵 TROVATO con query '{q}': {mp3_link}")
                        return track.get("pageURL"), mp3_link
        except Exception as e:
            print(f"⚠️ Errore API Pixabay su '{q}': {e}")
            continue # Prova il prossimo tentativo

    # Se arriviamo qui, l'API ha fallito tutte le query. Usiamo il salvagente.
    print("🚨 MUSIC FALLBACK ACTIVATED: Using safe MP3.")
    return "Fallback Music", SAFE_FALLBACK_MP3