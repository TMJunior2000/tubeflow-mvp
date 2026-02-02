import requests
import streamlit as st
import random
import os

def get_api_keys():
    pex = os.getenv("PEXELS_API_KEY") or st.secrets.get("PEXELS_API_KEY")
    pix = os.getenv("PIXABAY_API_KEY") or st.secrets.get("PIXABAY_API_KEY")
    return pex, pix

# ... (Mantieni qui le funzioni get_hybrid_video, _search_pexels, _search_pixabay INVARIATE) ...
# ... (Se le hai perse dimmelo, ma dovresti averle dal messaggio precedente) ...
# ... INCOLLA QUI SOTTO SOLO LA PARTE AUDIO NUOVA ...

def get_pixabay_audio(genre: str, mood: str):
    """
    Usa SOLO l'API ufficiale di Pixabay Audio.
    Nessun fallback esterno.
    """
    _, pix_key = get_api_keys()
    
    if not pix_key:
        print("⚠️ Pixabay API Key mancante.")
        return None, None

    # Query ufficiale combinando Genre e Mood
    # Esempio URL: https://pixabay.com/api/audio/?key=...&q=cinematic+epic
    url = f"https://pixabay.com/api/audio/?key={pix_key}&q={genre}+{mood}&per_page=10"
    
    print(f"🎵 API CALL: {url}")

    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            hits = data.get("hits", [])
            
            if len(hits) > 0:
                # Prendiamo una traccia a caso tra le prime 10 per varietà
                track = random.choice(hits)
                
                # 'url' è il link al file MP3 (spesso CDN)
                mp3_link = track.get("url")
                page_link = track.get("pageURL")
                
                # Controlliamo che il link esista
                if mp3_link:
                    print(f"🎵 API SUCCESS: Found '{track.get('tags')}'")
                    return page_link, mp3_link
            else:
                print(f"⚠️ API returned 0 hits for {genre} + {mood}")
                
                # TENTATIVO DI SALVATAGGIO: Prova solo col Mood se la combinazione fallisce
                print("🔄 Retrying with Mood only...")
                url_retry = f"https://pixabay.com/api/audio/?key={pix_key}&q={mood}&per_page=5"
                r2 = requests.get(url_retry, timeout=10)
                if r2.status_code == 200:
                    hits2 = r2.json().get("hits", [])
                    if hits2:
                        track = random.choice(hits2)
                        return track.get("pageURL"), track.get("url")

    except Exception as e:
        print(f"⚠️ API Exception: {e}")

    return None, None