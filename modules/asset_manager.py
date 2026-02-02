import requests
import streamlit as st
import random
import os

def get_api_keys():
    pex = os.getenv("PEXELS_API_KEY") or st.secrets.get("PEXELS_API_KEY")
    pix = os.getenv("PIXABAY_API_KEY") or st.secrets.get("PIXABAY_API_KEY")
    return pex, pix

# ==========================================
# 🎥 SEZIONE VIDEO (Qualità + Breadcrumbs)
# ==========================================
def get_hybrid_video(keyword: str, vibe: str, orientation: str):
    pex_key, pix_key = get_api_keys()
    
    # 1. Pulizia e Breadcrumbs
    base_keyword = keyword.replace("Vertical", "").replace("Portrait", "").replace("Landscape", "").strip()
    words = base_keyword.split()
    breadcrumbs = []
    for i in range(len(words), 0, -1):
        breadcrumbs.append(" ".join(words[:i]))
    if not breadcrumbs: breadcrumbs = [base_keyword]

    print(f"🔍 Search Strategy: {breadcrumbs}")

    for attempt, query in enumerate(breadcrumbs):
        match_label = "🟢 EXACT MATCH" if attempt == 0 else "🟡 BROAD MATCH"
        
        # --- PEXELS (Gestione HD) ---
        vid_pex = None
        if pex_key:
            try:
                h = {"Authorization": pex_key}
                u = f"https://api.pexels.com/videos/search?query={query}&per_page=1&orientation={orientation}"
                r = requests.get(u, headers=h, timeout=5)
                if r.status_code == 200:
                    d = r.json()
                    if d.get("videos"):
                        v = d["videos"][0]
                        # Cerchiamo qualità HD (minimo 720p)
                        dl = v['video_files'][0]['link']
                        for f in v['video_files']:
                            if f['quality'] == 'hd' and f['width'] >= 720: 
                                dl = f['link']; break
                        vid_pex = {"source":"Pexels", "preview": v['video_files'][0]['link'], "download": dl}
            except: pass

        # --- PIXABAY (Gestione Qualità Documentata) ---
        vid_pix = None
        if pix_key:
            try:
                # Documentazione: Video non supportano filtro orientation, lo aggiungiamo alla query
                pix_query = f"{query} vertical" if orientation == "portrait" else query
                # Documentazione: q deve essere URL encoded (requests lo fa da solo)
                u = f"https://pixabay.com/api/videos/?key={pix_key}&q={pix_query}&per_page=3"
                
                r = requests.get(u, timeout=5)
                if r.status_code == 200:
                    d = r.json()
                    if int(d.get('totalHits', 0)) > 0:
                        v = d['hits'][0]
                        
                        # SCELTA RISOLUZIONE (Evitiamo 'tiny')
                        # La doc dice che 'medium' è quasi sempre disponibile ed è 720p/1080p
                        if 'medium' in v['videos'] and v['videos']['medium']['size'] > 0:
                            dl = v['videos']['medium']['url']
                        elif 'large' in v['videos'] and v['videos']['large']['size'] > 0:
                             dl = v['videos']['large']['url']
                        elif 'small' in v['videos']:
                            dl = v['videos']['small']['url']
                        else:
                            dl = v['videos']['tiny']['url'] # Ultima spiaggia
                            
                        vid_pix = {"source":"Pixabay", "preview": v['videos']['tiny']['url'], "download": dl}
            except Exception as e:
                print(f"Pixabay Error: {e}")

        # Selezione Vincitore
        if vid_pex and vid_pix:
            winner = random.choice([vid_pex, vid_pix])
            return winner | {'match_type': match_label}
        if vid_pex: return vid_pex | {'match_type': match_label}
        if vid_pix: return vid_pix | {'match_type': match_label}
    
    return None

# ==========================================
# 🎵 SEZIONE AUDIO (API Ufficiale)
# ==========================================
def get_pixabay_audio(genre: str, mood: str):
    """
    Restituisce (PageURL, Mp3URL) oppure (None, ErrorMsg).
    """
    _, pix_key = get_api_keys()
    
    if not pix_key:
        return None, "ERRORE: API Key mancante."

    # Documentazione: category=genre + q=mood
    url = f"https://pixabay.com/api/audio/?key={pix_key}&q={genre}+{mood}&per_page=5"
    
    try:
        # Aggiungo headers anche qui per evitare blocchi preventivi (Rate Limit check)
        h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        r = requests.get(url, headers=h, timeout=10)
        
        if r.status_code != 200:
            return None, f"HTTP ERROR {r.status_code}: {r.text}"

        data = r.json()
        hits = data.get("hits", [])
        
        if len(hits) == 0:
            # Fallback intelligente: prova solo il mood
            r2 = requests.get(f"https://pixabay.com/api/audio/?key={pix_key}&q={mood}", headers=h, timeout=10)
            if r2.status_code == 200 and r2.json().get("hits"):
                track = random.choice(r2.json()["hits"])
                return track.get("pageURL"), track.get("url")
            else:
                return None, f"NESSUN RISULTATO per '{genre} + {mood}'"

        track = random.choice(hits)
        return track.get("pageURL"), track.get("url")

    except Exception as e:
        return None, f"EXCEPTION: {str(e)}"