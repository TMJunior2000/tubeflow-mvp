import requests
import streamlit as st
import random
import os

# --- 1. CONFIGURAZIONE ---
def get_api_keys():
    """Recupera le chiavi API (Admin Keys)"""
    pex = os.getenv("PEXELS_API_KEY") or st.secrets.get("PEXELS_API_KEY")
    pix = os.getenv("PIXABAY_API_KEY") or st.secrets.get("PIXABAY_API_KEY")
    return pex, pix

# --- 2. MOTORE IBRIDO (IL CERVELLO) ---
def get_hybrid_video(keyword: str, vibe: str, orientation: str):
    """
    Cerca video usando la strategia 'Breadcrumb' (A cipolla).
    Interroga Pexels e Pixabay con PARI IMPORTANZA.
    """
    pex_key, pix_key = get_api_keys()
    
    # Pulizia Keyword (Rimuoviamo comandi tecnici se l'IA li ha lasciati)
    base_keyword = keyword.replace("Vertical", "").replace("Portrait", "").replace("Landscape", "").strip()
    
    # Generazione Breadcrumbs (Le varianti di ricerca)
    # Es: "Penguin Climbing Snow" -> ["Penguin Climbing Snow", "Penguin Climbing", "Penguin"]
    words = base_keyword.split()
    breadcrumbs = []
    for i in range(len(words), 0, -1):
        breadcrumbs.append(" ".join(words[:i]))
    
    if not breadcrumbs: breadcrumbs = [base_keyword] # Fallback sicurezza

    print(f"🔍 Breadcrumbs Strategy: {breadcrumbs}")

    # --- CICLO DI RICERCA (Step by Step) ---
    for attempt, query in enumerate(breadcrumbs):
        
        # Definiamo la precisione del match per l'utente
        is_last_attempt = (attempt == len(breadcrumbs) - 1) and len(breadcrumbs) > 1
        if attempt == 0:
            match_label = "🟢 EXACT MATCH"
        elif is_last_attempt:
            match_label = "🟠 SUBJECT ONLY"
        else:
            match_label = "🟡 BROAD MATCH"

        # Interroghiamo i due motori in parallelo
        result_pexels = _search_pexels(query, vibe, orientation, pex_key) if pex_key else None
        result_pixabay = _search_pixabay(query, vibe, orientation, pix_key) if pix_key else None

        # --- LOGICA "EQUAL IMPORTANCE" (Spareggio) ---
        if result_pexels and result_pixabay:
            # Entrambi hanno trovato il video per questa query!
            # Scegliamo a caso per dare varietà (50% Pexels, 50% Pixabay)
            winner = random.choice([result_pexels, result_pixabay])
            winner['match_type'] = match_label
            winner['used_query'] = query
            return winner
        
        # Se ne abbiamo trovato solo uno, vinci lui
        if result_pexels:
            result_pexels['match_type'] = match_label
            result_pexels['used_query'] = query
            return result_pexels
            
        if result_pixabay:
            result_pixabay['match_type'] = match_label
            result_pixabay['used_query'] = query
            return result_pixabay

        # Se nessuno ha trovato nulla, il ciclo continua con la prossima "briciola" più corta...

    return None # Nessun risultato nemmeno con 1 parola

# --- 3. MOTORE PEXELS ---
def _search_pexels(keyword, vibe, orientation, key):
    headers = {"Authorization": key}
    
    # Color Mapping: Traduce lo stile in codici esadecimali per Pexels
    color_map = {
        "Dark Cinematic": "000000",
        "Luxury": "DAA520",     # Oro
        "Tech": "0000FF",       # Blu Elettrico
        "Minimalist": "E6E6FA", # Bianco/Lavanda
        "Nature": "228B22"      # Verde
    }
    # Cerca se la vibe è nella mappa (es. "Dark" in "Dark Cinematic")
    color_hex = next((v for k, v in color_map.items() if k in vibe), "")
    color_param = f"&color={color_hex}" if color_hex else ""

    url = f"https://api.pexels.com/videos/search?query={keyword}&per_page=1&orientation={orientation}{color_param}"
    
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("videos"):
                vid = data["videos"][0]
                
                # Cerchiamo il file migliore (HD ma non 4K pesante, ideale 1080p o 720p)
                # Pexels restituisce una lista 'video_files'. Cerchiamo quality='hd'.
                best_link = vid['video_files'][0]['link'] # Default
                for f in vid['video_files']:
                    # Preferiamo HD con larghezza > 720 (quindi 1080p o 720p)
                    if f['quality'] == 'hd' and f['width'] >= 720:
                        best_link = f['link']
                        break
                
                return {
                    "source": "Pexels",
                    "author": vid['user']['name'],
                    "preview": vid['video_files'][0]['link'], # Link leggero per preview
                    "download": best_link, # Link alta qualità per download
                    "video_link": vid['url'] # Link alla pagina originale
                }
    except Exception as e:
        print(f"Pexels Error: {e}")
    return None

# --- 4. MOTORE PIXABAY ---
def _search_pixabay(keyword, vibe, orientation, key):
    # Pixabay API Video non ha il filtro 'orientation', lo simuliamo nel testo
    suffix = " vertical" if orientation == "portrait" else ""
    
    # Se la vibe è Dark, aiutiamo Pixabay aggiungendo 'dark' o 'night'
    vibe_txt = " dark" if "Dark" in vibe else ""
    
    query = f"{keyword}{vibe_txt}{suffix}"
    url = f"https://pixabay.com/api/videos/?key={key}&q={query}&video_type=film&per_page=3"
    
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if int(data.get("totalHits", 0)) > 0:
                # Pixabay ordina per rilevanza, prendiamo il primo
                vid = data["hits"][0]
                
                # Gestione Risoluzioni (tiny, small, medium, large)
                # 'medium' è solitamente 720p/1080p. 'tiny' è per preview veloce.
                preview_url = vid["videos"]["tiny"]["url"]
                download_url = vid["videos"]["medium"]["url"]
                
                # Fallback se medium manca (raro)
                if not download_url: download_url = vid["videos"]["small"]["url"]

                return {
                    "source": "Pixabay",
                    "author": f"User {vid['user_id']}",
                    "preview": preview_url,
                    "download": download_url,
                    "video_link": vid['pageURL']
                }
    except Exception as e:
        print(f"Pixabay Error: {e}")
    return None

# --- 5. MOTORE AUDIO ---
def get_background_music(vibe: str):
    _, pix_key = get_api_keys()
    if not pix_key: return None, None
    
    # Mapping Vibe -> Music Tags
    tag = "ambient"
    if "Fast Paced" in vibe: tag = "action"
    elif "Dark" in vibe: tag = "horror"
    elif "Luxury" in vibe: tag = "fashion"
    elif "Tech" in vibe: tag = "science"
    
    url = f"https://pixabay.com/api/?key={pix_key}&q={tag}&category=music&per_page=3"
    
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if int(data.get("totalHits", 0)) > 0:
                track = random.choice(data["hits"])
                # L'API Music di Pixabay è in beta, il campo audio è spesso in 'videos'->'large' nei json sporchi
                # o direttamente keys come 'audio'. Per sicurezza, controlliamo cosa c'è.
                # Nota: Dai test recenti, Pixabay music a volte richiede scraping, 
                # ma per ora usiamo il 'pageURL' che è sicuro.
                # Se l'API restituisce un URL diretto mp3 (spesso 'previewURL' in docs vecchie), usalo.
                return track.get("pageURL"), track.get("pageURL") 
    except: pass
    return None, None