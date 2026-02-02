import requests
import streamlit as st
import random
import os

def get_api_keys():
    pex = os.getenv("PEXELS_API_KEY") or st.secrets.get("PEXELS_API_KEY")
    pix = os.getenv("PIXABAY_API_KEY") or st.secrets.get("PIXABAY_API_KEY")
    return pex, pix

# ==========================================
# 🎥 SEZIONE VIDEO (Logica "Best Match Competitivo")
# ==========================================
def get_hybrid_video(keyword: str, vibe: str, orientation: str):
    pex_key, pix_key = get_api_keys()
    
    # 1. Preparazione Keyword (es: "Samurai Rain")
    base_keyword = keyword.replace("Vertical", "").replace("Portrait", "").replace("Landscape", "").strip()
    words = base_keyword.split()
    
    # 2. Breadcrumbs: ["Samurai Rain", "Samurai"]
    # Cerchiamo prima la frase intera. Se non troviamo NULLA, scendiamo al generico.
    breadcrumbs = []
    for i in range(len(words), 0, -1):
        breadcrumbs.append(" ".join(words[:i]))
    if not breadcrumbs: breadcrumbs = [base_keyword]

    print(f"🔍 Search Strategy: {breadcrumbs}")

    for attempt, query in enumerate(breadcrumbs):
        match_label = "🟢 EXACT MATCH" if attempt == 0 else "🟡 BROAD MATCH"
        print(f"   👉 Testing Query: '{query}'...")

        # --- FASE 1: INTERROGAZIONE PARALLELA ---
        # Chiediamo a TUTTI E DUE se hanno questa query specifica.
        
        # Pexels Search
        vid_pex = None
        if pex_key:
            vid_pex = _search_pexels(query, orientation, pex_key)

        # Pixabay Search
        vid_pix = None
        if pix_key:
            vid_pix = _search_pixabay(query, orientation, pix_key)

        # --- FASE 2: IL DUELLO (Chi ha il video migliore?) ---
        
        # CASO A: Entrambi hanno trovato la query specifica (es. "Samurai Rain")
        if vid_pex and vid_pix:
            # Qui usiamo Pexels come tie-breaker per la qualità fotografica, 
            # MA siamo sicuri che entrambi sono pertinenti (hanno matchato la query).
            print(f"      🏆 WINNER: Pexels (Quality Tie-Break on '{query}')")
            return vid_pex | {'match_type': match_label}
        
        # CASO B: Solo Pexels l'ha trovato
        if vid_pex:
            print(f"      🏆 WINNER: Pexels (Exclusive match on '{query}')")
            return vid_pex | {'match_type': match_label}
            
        # CASO C: Solo Pixabay l'ha trovato (IL TUO CASO)
        # Se Pixabay ha "Samurai Rain" e Pexels no, QUI VINCE PIXABAY.
        # Non passiamo alla query generica "Samurai". Ci teniamo la pioggia di Pixabay.
        if vid_pix:
            print(f"      🏆 WINNER: Pixabay (Exclusive match on '{query}')")
            return vid_pix | {'match_type': match_label}
            
        # CASO D: Nessuno ha trovato niente -> Il ciclo continua con la prossima keyword più corta.
    
    return None

# --- Helper Pexels ---
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
                # Filtro HD
                for f in v['video_files']:
                    if f['quality'] == 'hd' and f['width'] >= 720: 
                        dl = f['link']; break
                return {"source":"Pexels", "preview": v['video_files'][0]['link'], "download": dl}
    except Exception as e:
        print(f"Pexels Err: {e}")
    return None

# --- Helper Pixabay ---
def _search_pixabay(keyword, orientation, key):
    try:
        pix_query = f"{keyword} vertical" if orientation == "portrait" else keyword
        pix_query = pix_query.replace(" ", "+") # Encoding manuale sicuro
        u = f"https://pixabay.com/api/videos/?key={key}&q={pix_query}&per_page=3"
        
        r = requests.get(u, timeout=5)
        if r.status_code == 200:
            d = r.json()
            if int(d.get('totalHits', 0)) > 0:
                v = d['hits'][0]
                # Scelta qualità: Evitiamo Tiny
                dl = v['videos']['tiny']['url'] # Fallback
                if 'medium' in v['videos'] and v['videos']['medium']['size'] > 0: 
                    dl = v['videos']['medium']['url']
                elif 'small' in v['videos']: 
                    dl = v['videos']['small']['url']
                    
                return {"source":"Pixabay", "preview": v['videos']['tiny']['url'], "download": dl}
    except Exception as e:
        print(f"Pixabay Err: {e}")
    return None

# ==========================================
# 🎵 SEZIONE AUDIO (No Headers in ricerca = No 403)
# ==========================================
def get_pixabay_audio(genre: str, mood: str):
    _, pix_key = get_api_keys()
    if not pix_key: return None, "ERRORE: API Key mancante."

    # Ricerca SENZA headers browser (evita 403)
    url = f"https://pixabay.com/api/audio/?key={pix_key}&q={genre}+{mood}&per_page=10"
    
    try:
        r = requests.get(url, timeout=10) # Niente headers qui!
        
        if r.status_code != 200:
            return None, f"HTTP ERROR {r.status_code}"

        data = r.json()
        hits = data.get("hits", [])
        
        if len(hits) == 0:
            # Retry solo mood
            r2 = requests.get(f"https://pixabay.com/api/audio/?key={pix_key}&q={mood}", timeout=10)
            if r2.status_code == 200 and r2.json().get("hits"):
                track = random.choice(r2.json()["hits"])
                return track.get("pageURL"), track.get("url")
            else:
                return None, f"NESSUN RISULTATO"

        track = random.choice(hits)
        return track.get("pageURL"), track.get("url")

    except Exception as e:
        return None, f"EXCEPTION: {str(e)}"