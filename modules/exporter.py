import zipfile
from io import BytesIO
import requests
import os

# --- HEADERS UFFICIALI PER EVITARE BLOCCO CDN ---
def get_browser_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://pixabay.com/", # Fondamentale: Pixabay controlla che la richiesta arrivi 'dal suo sito'
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "*/*"
    }

def generate_davinci_xml(project_name, scenes, orientation, music_path=None, voice_path=None, fps=30):
    # (Logica XML standard - copia quella del messaggio precedente se serve, 
    # l'importante è che scriva i path corretti Assets/Background_Music.mp3)
    # ... PER BREVITÀ USO LA LOGICA STANDARD ...
    total_duration = sum(s['duration'] for s in scenes)
    width, height = (1080, 1920) if orientation == "portrait" else (1920, 1080)

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.8">
    <resources>
        <format id="r1" name="FFVideoFormat{height}p{fps}" frameDuration="1/{fps}s" width="{width}" height="{height}" colorSpace="1-1-1 (Rec. 709)"/>
"""
    r_id = 2
    music_rid = f"r{r_id}" if music_path else None
    if music_path: 
        xml += f'        <asset id="{music_rid}" name="Music" src="./Assets/Background_Music.mp3" start="0s" duration="{total_duration}s" hasVideo="0" hasAudio="1" audioSources="1" audioChannels="2" />\n'; r_id+=1
    
    voice_rid = f"r{r_id}" if voice_path else None
    if voice_path: 
        xml += f'        <asset id="{voice_rid}" name="Voice" src="./Assets/Voiceover.mp3" start="0s" duration="{total_duration}s" hasVideo="0" hasAudio="1" audioSources="1" audioChannels="1" />\n'; r_id+=1

    xml += f"""    </resources>
    <library>
        <event name="{project_name}">
            <project name="{project_name}">
                <sequence format="r1" duration="{total_duration}s" tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="48k">
                    <spine>
"""
    offset = 0
    for i, scene in enumerate(scenes):
        clean_name = f"{i+1:02d}_Clip.mp4"
        dur = scene['duration']
        xml += f"""                        <clip name="{clean_name}" offset="{offset}s" duration="{dur}s" start="0s">
                            <note>{scene['voiceover']}</note>
                            <video offset="0s" ref="r1" duration="{dur}s" start="0s"/>"""
        
        if i == 0:
            if voice_rid: xml += f'<clip lane="-1" offset="0s" ref="{voice_rid}" duration="{total_duration}s" start="0s"><audio role="dialogue"/></clip>'
            if music_rid: xml += f'<clip lane="-2" offset="0s" ref="{music_rid}" duration="{total_duration}s" start="0s"><audio role="music"/></clip>'
        
        xml += "                        </clip>\n"
        offset += dur

    xml += """                    </spine>
                </sequence>
            </project>
        </event>
    </library>
</fcpxml>"""
    return xml

def create_smart_package(scenes, orientation, music_url=None, voiceover_path=None):
    zip_buffer = BytesIO()
    has_music = False
    has_voice = False

    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
        
        # 1. VIDEO
        for i, scene in enumerate(scenes):
            url = scene.get('video_link') or scene.get('download')
            if url:
                try:
                    r = requests.get(url, headers=get_browser_headers(), timeout=20)
                    if r.status_code == 200:
                        zf.writestr(f"Assets/{i+1:02d}_Clip.mp4", r.content)
                except: pass # Gestione errori base

        # 2. MUSICA (L'INTERVENTO CHIRURGICO)
        if music_url:
            try:
                real_url = music_url[1] if isinstance(music_url, tuple) else music_url
                print(f"⬇️ DOWNLOADING API MUSIC: {real_url}")
                
                # USIAMO HEADERS + STREAMING PER EVITARE MEMORY LEAK E BLOCCHI
                # 'allow_redirects=True' segue se il CDN sposta il file
                r = requests.get(real_url, headers=get_browser_headers(), timeout=30, allow_redirects=True, stream=True)
                
                if r.status_code == 200:
                    # Leggiamo il contenuto (per file < 10MB è ok farlo in memoria)
                    music_content = r.content
                    if len(music_content) > 1000: # Controllo che non sia un file errore vuoto
                        zf.writestr("Assets/Background_Music.mp3", music_content)
                        has_music = True
                        print("✅ Musica scaricata da API Ufficiale.")
                    else:
                        print("❌ File troppo piccolo (probabile errore API).")
                else:
                    # Debug file nello zip
                    zf.writestr("Assets/API_ERROR.txt", f"HTTP {r.status_code} on {real_url}")
                    print(f"❌ Errore HTTP {r.status_code}")

            except Exception as e:
                zf.writestr("Assets/API_EXCEPTION.txt", str(e))
                print(f"❌ Eccezione: {e}")

        # 3. VOICEOVER
        if voiceover_path and os.path.exists(voiceover_path):
            with open(voiceover_path, "rb") as f: zf.writestr("Assets/Voiceover.mp3", f.read())
            has_voice = True

        # 4. XML
        xml = generate_davinci_xml("TubeFlow", scenes, orientation, "Assets/Background_Music.mp3" if has_music else None, "Assets/Voiceover.mp3" if has_voice else None)
        zf.writestr(f"Project_{orientation}.fcpxml", xml)
        
        script = "\n".join([f"SCENE {s['scene_number']}: {s['voiceover']}" for s in scenes])
        zf.writestr("Script.txt", script)

    return zip_buffer.getvalue()