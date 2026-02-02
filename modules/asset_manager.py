import requests
import streamlit as st
import random
import os

# --- CONFIGURAZIONE E UTILS ---
def get_api_keys():
    """Recupera le chiavi API dai secrets di Streamlit o variabili d'ambiente."""
    pex = os.getenv("PEXELS_API_KEY") or st.secrets.get("PEXELS_API_KEY")
    pix = os.getenv("PIXABAY_API_KEY") or st.secrets.get("PIXABAY_API_KEY")
    return pex, pix

def get_hybrid_video(keyword: str, vibe: str, orientation: str):
    """
    MOTORE DI RICERCA IBRIDO CON BREADCRUMB STRATEGY.
    
    1. Pulisce la keyword.
    2. Crea le varianti (Breadcrumbs): "Lion Savanna Golden" -> "Lion Savanna" -> "Lion".
    3. Per ogni variante, cerca su Pexels E Pixabay.
    4. Restituisce il primo risultato utile con i metadati di precisione.
    """
    pex_key, pix_key = get_api_keys()
    
    # 1. Pulizia Keyword (Rimuoviamo istruzioni tecniche se presenti)
    base_keyword = keyword.replace("Vertical", "").replace("Portrait", "").replace("Landscape", "").strip()
    
    # 2. Generazione Breadcrumbs (Le "Briciole di pane")
    words = base_keyword.split()
    breadcrumbs = []
    
    # Crea varianti progressivamente più corte
    # Es: ["Penguin Mountain Snow", "Penguin Mountain", "Penguin"]
    for i in range(len(words), 0, -1):
        query_variant = " ".join(words[:i])
        breadcrumbs.append(query_variant)
    
    # Fallback per keyword vuote o singole
    if not breadcrumbs: breadcrumbs = [base_keyword]

    print(f"🔍 Breadcrumbs per '{keyword}': {breadcrumbs}")

    # 3. Ciclo di Ricerca Competitivo
    for attempt, query in enumerate(breadcrumbs):
        # Determina il tipo di match per la UI
        is_last_attempt = (attempt == len(breadcrumbs) - 1) and len(breadcrumbs) > 1
        
        if attempt == 0:
            match_type = "🟢 EXACT MATCH"
        elif is_last_attempt:
            match_type = "🟠 SUBJECT ONLY"
        else:
            match_type = "🟡 BROAD MATCH"

        # --- TENTATIVO PEXELS ---
        if pex_key:
            vid = _search_pexels(query, vibe, orientation, pex_key)
            if vid:
                return vid | {
                    "match_type": match_type,
                    "used_query": query,
                    "source": "Pexels"
                }

        # --- TENTATIVO PIXABAY ---
        if pix_key:
            vid = _search_pixabay(query, vibe, orientation, pix_key)
            if vid:
                return vid | {
                    "match_type": match_type,
                    "used_query": query,
                    "source": "Pixabay"
                }
    
    # Se arriviamo qui, nessun motore ha trovato nulla (nemmeno con 1 parola)
    return None

# --- MOTORE PEXELS ---
def _search_pexels(keyword, vibe, orientation, key):
    headers = {"Authorization": key}
    
    # Mappatura Colori Intelligente (The "Vibe Hack")
    # Pexels indicizza molto bene i colori predominanti.
    color_map = {
        "Dark Cinematic": "000000", # Nero
        "Luxury": "DAA520",         # Oro (GoldenRod)
        "Tech": "0000FF",           # Blu
        "Minimalist": "E6E6FA",     # Lavanda/Bianco
        "Nature": "228B22",         # Verde foresta
        "Fast Paced": ""            # Nessun colore specifico
    }
    
    # Se la vibe corrisponde a un colore, lo aggiungiamo
    # Nota: Usiamo una corrispondenza parziale sulla stringa vibe
    color_code = ""
    for v_key, v_code in color_map.items():
        if v_key in vibe:
            color_code = v_code
            break
            
    color_param = f"&color={color_code}" if color_code else ""
    
    # Costruzione URL Pexels
    url = f"https://api.pexels.com/videos/search?query={keyword}&per_page=1&orientation={orientation}{color_param}"
    
    try:
        r = requests.get(url, headers=headers, timeout=4)
        if r.status_code == 200:
            data = r.json()
            if data.get("videos") and len(data["videos"]) > 0:
                vid = data["videos"][0]
                
                # Cerchiamo il link HD migliore (spesso 720p o 1080p)
                # Fallback sul primo disponibile se non trova 'hd'
                download_link = vid['video_files'][0]['link']
                for f in vid['video_files']:
                    if f['quality'] == 'hd' and f['width'] >= 1080: # Preferiamo 1080p
                        download_link = f['link']
                        break
                
                return {
                    "preview": vid['video_files'][0]['link'], # Solitamente buono per preview
                    "download": download_link,
                    "author": vid['user']['name'],
                    "source_id": "Pexels"
                }
    except Exception as e:
        print(f"Pexels Error: {e}")
    return None

# --- MOTORE PIXABAY ---
def _search_pixabay(keyword, vibe, orientation, key):
    # Pixabay non ha filtri orientation/colori nativi per video avanzati,
    # quindi li simuliamo aggiungendoli alla query testuale.
    
    suffix = " vertical" if orientation == "portrait" else ""
    
    # Aggiungiamo tag di atmosfera alla query se necessario
    vibe_tag = ""
    if "Dark" in vibe: vibe_tag = " dark"
    elif "Luxury" in vibe: vibe_tag = " gold"
    elif "Nature" in vibe: vibe_tag = " nature"
    
    # Query finale combinata
    query = f"{keyword}{vibe_tag}{suffix}"
    
    # Endpoint Video Pixabay
    url = f"https://pixabay.com/api/videos/?key={key}&q={query}&video_type=film&per_page=3"
    
    try:
        r = requests.get(url, timeout=4)
        if r.status_code == 200:
            data = r.json()
            if int(data.get("totalHits", 0)) > 0:
                # Prendiamo il primo risultato
                vid = data["hits"][0]
                
                # Pixabay offre: tiny, small, medium, large
                # 'medium' è di solito un buon compromesso (spesso 720p/1080p)
                # 'tiny' è perfetto per la preview streamable
                
                return {
                    "preview": vid["videos"]["tiny"]["url"],
                    "download": vid["videos"]["medium"]["url"],
                    "author": f"PixabayUser_{vid['user_id']}",
                    "source_id": "Pixabay"
                }
    except Exception as e:
        print(f"Pixabay Error: {e}")
    return None

# --- MOTORE AUDIO (PIXABAY MUSIC) ---
def get_background_music(vibe: str):
    """
    Scarica una traccia audio MP3 da Pixabay basandosi sulla Vibe.
    """
    _, pix_key = get_api_keys()
    if not pix_key: return None, None
    
    # Mapping Vibe -> Tag Musicale Pixabay
    tag = "ambient" # Default
    if "Fast Paced" in vibe: tag = "upbeat"
    elif "Dark" in vibe: tag = "cinematic horror"
    elif "Luxury" in vibe: tag = "corporate"
    elif "Minimalist" in vibe: tag = "chill"
    elif "Tech" in vibe: tag = "electronic"
    
    url = f"https://pixabay.com/api/?key={pix_key}&q={tag}&category=music&per_page=5"
    
    try:
        r = requests.get(url, timeout=4)
        if r.status_code == 200:
            data = r.json()
            if int(data.get("totalHits", 0)) > 0:
                # Scegliamo a caso tra i primi 5 per varietà
                track = random.choice(data["hits"])
                # Pixabay Audio restituisce 'pageURL' per i credits
                # e un link diretto che spesso è nel campo 'preview' o simile
                # Nota: l'API audio di Pixabay è in beta e la struttura varia,
                # ma spesso track['videos']['large']['url'] nei risultati audio è l'mp3
                # Se non c'è, usiamo una logica di fallback o cerchiamo il campo giusto.
                # Per ora assumiamo che la struttura JSON dei risultati audio sia simile ai video
                # o che ci sia un campo audio diretto.
                
                # FIX COMUNE PIXABAY AUDIO:
                # Spesso il file audio è sotto 'audio' o top level keys.
                # In base all'analisi JSON standard:
                # track["pageURL"] è la pagina
                # track.get("previewURL") è spesso l'mp3 preview.
                return track.get("pageURL"), track.get("previewURL") # previewURL è spesso l'mp3 completo per Pixabay
    except Exception as e:
        print(f"Audio Error: {e}")
    
    return None, None