import requests
import streamlit as st
import os

# --- COSTANTE: Maschera da Browser per evitare blocchi ---
FAKE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.google.com/"
}

def get_api_keys():
    # Cerca prima in ENV (locale), poi in SECRETS (Cloud)
    pex = os.getenv("PEXELS_API_KEY") or st.secrets.get("PEXELS_API_KEY")
    pix = os.getenv("PIXABAY_API_KEY") or st.secrets.get("PIXABAY_API_KEY")
    return pex, pix

def validate_video_content(video_metadata, required_keyword):
    """
    Controlla se il video contiene davvero la parola chiave richiesta.
    """
    required = required_keyword.lower().strip()
    
    # Uniamo tutti i testi disponibili in una stringa di controllo
    check_text = (
        str(video_metadata.get('url', '')) + " " + 
        str(video_metadata.get('tags', '')) + " " + 
        str(video_metadata.get('id', ''))
    ).lower()

    if required not in check_text:
        return False
    return True

def get_hybrid_video(keyword: str, orientation: str, excluded_urls=None):
    if excluded_urls is None: excluded_urls = []
    pex_key, pix_key = get_api_keys()
    
    if not pex_key and not pix_key:
        print("⚠️ NESSUNA API KEY TROVATA!")
        return None

    query = keyword.lower().strip()
    anchor_subject = query.split()[0] 
    
    candidates = []

    # 1. PEXELS SEARCH
    if pex_key:
        try:
            # Uniamo l'Authorization con il FAKE HEADER
            h = {"Authorization": pex_key}
            h.update(FAKE_HEADERS) 
            
            u = f"https://api.pexels.com/videos/search?query={query}&per_page=10&orientation={orientation}"
            r = requests.get(u, headers=h, timeout=10)
            
            if r.status_code == 200:
                data = r.json()
                for v in data.get("videos", []):
                    # Validazione
                    if not validate_video_content(v, anchor_subject): continue 

                    link = None
                    for f in v['video_files']:
                        if f['quality'] == 'hd' and f['width'] >= 720: 
                            link = f['link']; break
                    if not link and v['video_files']: link = v['video_files'][0]['link']
                    
                    if link and link not in excluded_urls:
                        candidates.append({
                            "score": 10, 
                            "source": "Pexels", 
                            "preview": v['video_files'][0]['link'], 
                            "download": link
                        })
            else:
                print(f"Pexels Error: {r.status_code}")
        except Exception as e: 
            print(f"Pexels Exception: {e}")

    # 2. PIXABAY SEARCH
    if pix_key:
        try:
            p_orient = "vertical" if orientation == "portrait" else "horizontal"
            params = {"key": pix_key, "q": query, "per_page": 10, "orientation": p_orient, "video_type": "film"}
            
            # Aggiungiamo headers anche qui
            r = requests.get("https://pixabay.com/api/videos/", params=params, headers=FAKE_HEADERS, timeout=10)
            
            if r.status_code == 200:
                data = r.json()
                for v in data.get('hits', []):
                    # Validazione
                    if not validate_video_content(v, anchor_subject): continue 

                    score = 20 
                    link = v['videos'].get('medium', {}).get('url') or v['videos'].get('large', {}).get('url')
                    
                    if link and link not in excluded_urls:
                        candidates.append({
                            "score": score, 
                            "source": "Pixabay", 
                            "preview": v['videos']['tiny']['url'], 
                            "download": link
                        })
            else:
                print(f"Pixabay Error: {r.status_code}")
        except Exception as e:
            print(f"Pixabay Exception: {e}")

    if not candidates: return None
    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates[0]

def download_video(url, filename):
    """
    Scarica il video gestendo User-Agent e creazione cartelle.
    """
    if not os.path.exists("temp_videos"):
        os.makedirs("temp_videos")
    
    path = os.path.join("temp_videos", filename)
    
    try:
        # FONDAMENTALE: Usare gli headers anche nel download!
        response = requests.get(url, headers=FAKE_HEADERS, stream=True, timeout=20)
        
        if response.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024):
                    if chunk: f.write(chunk)
            return path
        else:
            print(f"Errore Download {filename}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Eccezione Download {filename}: {e}")
        return None