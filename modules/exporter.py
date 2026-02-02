import zipfile
from io import BytesIO
import requests
import os
import streamlit as st

# --- FUNZIONE DOWNLOAD ANTI-403 ---
def download_asset_to_memory(url, asset_type="generic"):
    """
    Scarica un file URL in memoria (RAM) usando Headers che simulano un browser reale.
    Risolve il problema del 403 Forbidden su Streamlit Cloud.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://pixabay.com/", # LA CHIAVE: Pixabay vuole vedere che arrivi da casa sua
        "Accept": "*/*"
    }
    
    try:
        print(f"⬇️ Downloading {asset_type}: {url}")
        # stream=True è importante per file grandi, ma qui scarichiamo in RAM per lo ZIP
        r = requests.get(url, headers=headers, allow_redirects=True, timeout=30)
        
        if r.status_code == 200:
            # Controllo anti-fake (evita di scaricare pagine di errore HTML da 200 byte)
            if len(r.content) > 1000:
                return r.content
            else:
                print(f"⚠️ File troppo piccolo ({len(r.content)} bytes). Probabile errore HTML mascherato.")
                return None
        else:
            print(f"❌ HTTP Error {r.status_code} su {url}")
            return None
    except Exception as e:
        print(f"❌ Exception downloading {url}: {e}")
        return None

# --- GENERATORE XML (FCPXML 1.8) ---
def generate_davinci_xml(project_name, scenes, orientation, has_music, has_voice, fps=30):
    # Calcolo durate e risoluzioni
    total_duration = sum(s['duration'] for s in scenes)
    width, height = (1080, 1920) if orientation == "portrait" else (1920, 1080)

    # Header XML
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.8">
    <resources>
        <format id="r1" name="FFVideoFormat{height}p{fps}" frameDuration="1/{fps}s" width="{width}" height="{height}" colorSpace="1-1-1 (Rec. 709)"/>
"""
    r_id = 2
    
    # Asset Music (Se esiste)
    music_rid = None
    if has_music:
        music_rid = f"r{r_id}"
        xml += f'        <asset id="{music_rid}" name="Music" src="./Assets/Background_Music.mp3" start="0s" duration="{total_duration}s" hasVideo="0" hasAudio="1" audioSources="1" audioChannels="2" />\n'
        r_id += 1
    
    # Asset Voice (Se esiste)
    voice_rid = None
    if has_voice:
        voice_rid = f"r{r_id}"
        xml += f'        <asset id="{voice_rid}" name="Voice" src="./Assets/Voiceover.mp3" start="0s" duration="{total_duration}s" hasVideo="0" hasAudio="1" audioSources="1" audioChannels="1" />\n'
        r_id += 1

    xml += f"""    </resources>
    <library>
        <event name="{project_name}">
            <project name="{project_name}">
                <sequence format="r1" duration="{total_duration}s" tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="48k">
                    <spine>
"""
    
    # Timeline
    offset = 0
    for i, scene in enumerate(scenes):
        clean_name = f"{i+1:02d}_Clip.mp4"
        dur = scene['duration']
        
        xml += f"""                        <clip name="{clean_name}" offset="{offset}s" duration="{dur}s" start="0s">
                            <note>{scene['voiceover']}</note>
                            <video offset="0s" ref="r1" duration="{dur}s" start="0s"/>"""
        
        # Aggiungo audio solo alla prima clip (estesi per tutto il video)
        if i == 0:
            if voice_rid: 
                xml += f'<clip lane="-1" offset="0s" ref="{voice_rid}" duration="{total_duration}s" start="0s"><audio role="dialogue"/></clip>'
            if music_rid: 
                xml += f'<clip lane="-2" offset="0s" ref="{music_rid}" duration="{total_duration}s" start="0s"><audio role="music"/></clip>'
        
        xml += "                        </clip>\n"
        offset += dur

    xml += """                    </spine>
                </sequence>
            </project>
        </event>
    </library>
</fcpxml>"""
    return xml

# --- CREAZIONE PACCHETTO ZIP ---
def create_smart_package(scenes, orientation, music_url=None, voiceover_path=None):
    zip_buffer = BytesIO()
    
    # Flag per sapere cosa abbiamo scaricato davvero
    downloaded_music = False
    downloaded_voice = False

    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
        
        # 1. DOWNLOAD VIDEO
        for i, scene in enumerate(scenes):
            url = scene.get('video_link') or scene.get('download')
            if url:
                # Scarichiamo in RAM
                vid_data = download_asset_to_memory(url, f"Video {i+1}")
                if vid_data:
                    zf.writestr(f"Assets/{i+1:02d}_Clip.mp4", vid_data)
                else:
                    zf.writestr(f"Assets/ERROR_VIDEO_{i+1}.txt", f"Failed to download: {url}")

        # 2. DOWNLOAD MUSIC (Se c'è l'URL)
        if music_url:
            # Gestione se arriva come tupla (page, mp3) o stringa
            real_url = music_url[1] if isinstance(music_url, tuple) else music_url
            
            # Scarica in RAM
            music_data = download_asset_to_memory(real_url, "Background Music")
            
            if music_data:
                zf.writestr("Assets/Background_Music.mp3", music_data)
                downloaded_music = True
                print("✅ Musica inserita nello ZIP")
            else:
                zf.writestr("Assets/ERROR_MUSIC_DOWNLOAD.txt", f"Failed to download music from: {real_url}")
                print("❌ Fallito inserimento musica ZIP")

        # 3. INSERIMENTO VOICEOVER (File locale)
        if voiceover_path and os.path.exists(voiceover_path):
            with open(voiceover_path, "rb") as f:
                zf.writestr("Assets/Voiceover.mp3", f.read())
            downloaded_voice = True

        # 4. GENERAZIONE XML & SCRIPT
        # L'XML ora punta solo ai file che siamo riusciti a scaricare
        xml_content = generate_davinci_xml(
            "TubeFlow_Project", 
            scenes, 
            orientation, 
            has_music=downloaded_music, 
            has_voice=downloaded_voice
        )
        
        zf.writestr(f"Project_{orientation}.fcpxml", xml_content)
        
        script_content = "\n".join([f"SCENE {s['scene_number']}: {s['voiceover']}" for s in scenes])
        zf.writestr("Script.txt", script_content)

    return zip_buffer.getvalue()