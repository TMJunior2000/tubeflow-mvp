import requests
import streamlit as st
import random
import os

def get_api_keys():
    pex = os.getenv("PEXELS_API_KEY") or st.secrets.get("PEXELS_API_KEY")
    pix = os.getenv("PEXELS_API_KEY") or st.secrets.get("PIXABAY_API_KEY")
    return pex, pix

def get_hybrid_video(keyword: str, vibe: str, orientation: str):
    """
    STRATEGIA PARALLELA COMPETITIVA:
    Cerca su entrambi i motori contemporaneamente per la keyword esatta.
    Vince chi ha il risultato migliore.
    """
    pex_key, pix_key = get_api_keys()
    
    # 1. Pulizia Keyword
    clean_keyword = keyword.replace("Vertical", "").replace("Portrait", "").replace("Landscape", "").strip()
    
    # 2. RICERCA ESATTA (Round 1)
    # Cerchiamo "Penguin climbing mountain" su entrambi
    candidate_pexels = _search_pexels(clean_keyword, vibe, orientation, pex_key) if pex_key else None
    candidate_pixabay = _search_pixabay(clean_keyword, vibe, orientation, pix_key) if pix_key else None
    
    # 3. SPAREGGIO (Matchmaking)
    if candidate_pexels and candidate_pixabay:
        # Entrambi hanno il video esatto!
        # Tiriamo una moneta per dare varietà, oppure preferiamo Pexels per qualità 4K.
        # Qui usiamo random per dare "Stessa Importanza" come richiesto.
        winner = random.choice([candidate_pexels, candidate_pixabay])
        return winner | {"source": f"{winner['source_id']} (Exact Match)"}
    
    if candidate_pexels: return candidate_pexels | {"source": "Pexels (Exact Match)"}
    if candidate_pixabay: return candidate_pixabay | {"source": "Pixabay (Exact Match)"}

    # 4. FALLBACK SOGGETTO (Round 2)
    # Se siamo qui, nessuno ha trovato l'azione specifica. Cerchiamo il soggetto (es. "Penguin")
    subject_only = clean_keyword.split()[0]
    
    if len(clean_keyword.split()) > 1: # Solo se c'era più di una parola
        # Rilanciamo la ricerca parallela sul soggetto
        candidate_pexels = _search_pexels(subject_only, vibe, orientation, pex_key) if pex_key else None
        candidate_pixabay = _search_pixabay(subject_only, vibe, orientation, pix_key) if pix_key else None
        
        if candidate_pexels and candidate_pixabay:
            winner = random.choice([candidate_pexels, candidate_pixabay])
            return winner | {"source": f"{winner['source_id']} (Subject Only)"}
        
        if candidate_pexels: return candidate_pexels | {"source": "Pexels (Subject Only)"}
        if candidate_pixabay: return candidate_pixabay | {"source": "Pixabay (Subject Only)"}

    return None

# --- FUNZIONI DI RICERCA SINGOLE (Helper) ---

def _search_pexels(keyword, vibe, orientation, key):
    headers = {"Authorization": key}
    color = "&color=000000" if "Dark" in vibe else ""
    url = f"https://api.pexels.com/videos/search?query={keyword}&per_page=1&orientation={orientation}{color}"
    
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("videos") and len(data["videos"]) > 0:
                vid = data["videos"][0]
                link = next((f['link'] for f in vid['video_files'] if f['quality']=='hd'), vid['video_files'][0]['link'])
                return {
                    "preview": vid['video_files'][0]['link'],
                    "download": link,
                    "author": vid['user']['name'],
                    "source_id": "Pexels"
                }
    except Exception: pass
    return None

def _search_pixabay(keyword, vibe, orientation, key):
    # Pixabay trick per orientamento
    suffix = " vertical" if orientation == "portrait" else ""
    query = f"{keyword}{suffix}"
    url = f"https://pixabay.com/api/videos/?key={key}&q={query}&video_type=film&per_page=3"
    
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if int(data.get("totalHits", 0)) > 0:
                vid = data["hits"][0]
                return {
                    "preview": vid["videos"]["tiny"]["url"],
                    "download": vid["videos"]["medium"]["url"],
                    "author": f"PixabayUser_{vid['user_id']}",
                    "source_id": "Pixabay"
                }
    except Exception: pass
    return None

# (get_background_music rimane invariato...)
def get_background_music(vibe: str):
    _, pix_key = get_api_keys()
    if not pix_key: return None, None
    tag = "upbeat" if "Fast" in vibe else "cinematic"
    url = f"https://pixabay.com/api/?key={pix_key}&q={tag}&category=music&per_page=3"
    try:
        r = requests.get(url, timeout=3)
        data = r.json()
        if int(data.get("totalHits", 0)) > 0:
            track = random.choice(data["hits"])
            return track["pageURL"], track["videos"]["large"]["url"]
    except: pass
    return None, None