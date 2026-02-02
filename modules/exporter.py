import zipfile
from io import BytesIO
import requests
import os
import streamlit as st

def get_request_headers():
    """Si traveste da Browser per evitare blocchi 403 da Pexels/Pixabay"""
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://www.google.com/"
    }

def generate_davinci_xml(project_name, scenes, orientation, music_path=None, voice_path=None, fps=30):
    """
    Genera FCPXML 1.8 includendo Video, Musica e Voiceover.
    """
    total_duration = sum(s['duration'] for s in scenes)
    
    # Setup Risoluzione
    if orientation == "portrait":
        width, height = 1080, 1920
    else:
        width, height = 1920, 1080

    # Header XML
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.8">
    <resources>
        <format id="r1" name="FFVideoFormat{height}p{fps}" frameDuration="1/{fps}s" width="{width}" height="{height}" colorSpace="1-1-1 (Rec. 709)"/>
"""
    # --- 1. DEFINIZIONE RISORSE (ASSETS) ---
    resource_id_counter = 2
    
    music_res_id = None
    if music_path:
        music_res_id = f"r{resource_id_counter}"
        xml += f'        <asset id="{music_res_id}" name="Background_Music" src="./Assets/Background_Music.mp3" start="0s" duration="{total_duration}s" hasVideo="0" hasAudio="1" audioSources="1" audioChannels="2" />\n'
        resource_id_counter += 1

    voice_res_id = None
    if voice_path:
        voice_res_id = f"r{resource_id_counter}"
        xml += f'        <asset id="{voice_res_id}" name="Voiceover" src="./Assets/Voiceover.mp3" start="0s" duration="{total_duration}s" hasVideo="0" hasAudio="1" audioSources="1" audioChannels="1" />\n'
        resource_id_counter += 1

    xml += """    </resources>
    <library>
        <event name="{project_name}">
            <project name="{project_name}">
                <sequence format="r1" duration="{total_duration}s" tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="48k">
                    <spine>
"""
    
    # --- 2. TRACCIA VIDEO (SPINE) ---
    offset = 0
    for i, scene in enumerate(scenes):
        safe_keyword = "".join(c for c in scene['keyword'] if c.isalnum() or c in (' ', '_')).replace(' ', '_')
        filename = f"{i+1:02d}_{safe_keyword}.mp4"
        dur = scene['duration']
        
        xml += f"""
                        <clip name="{filename}" offset="{offset}s" duration="{dur}s" start="0s">
                            <note>{scene['voiceover']}</note>
                            <video offset="0s" ref="r1" duration="{dur}s" start="0s"/>
"""
        # --- 3. AGGANCIO AUDIO (CONNECTED CLIPS) ---
        if i == 0:
            # Voiceover (Priorità alta)
            if voice_res_id:
                xml += f"""
                            <clip name="Voiceover" lane="-1" offset="0s" ref="{voice_res_id}" duration="{total_duration}s" start="0s">
                                <audio offset="0s" ref="{voice_res_id}" duration="{total_duration}s" start="0s" role="dialogue"/>
                            </clip>"""
            
            # Musica (Priorità bassa, lane -2)
            if music_res_id:
                xml += f"""
                            <clip name="Music" lane="-2" offset="0s" ref="{music_res_id}" duration="{total_duration}s" start="0s">
                                <audio offset="0s" ref="{music_res_id}" duration="{total_duration}s" start="0s" role="music"/>
                            </clip>"""

        xml += "                        </clip>"
        offset += dur

    xml += """
                    </spine>
                </sequence>
            </project>
        </event>
    </library>
</fcpxml>"""
    
    return xml

def create_smart_package(scenes, orientation, music_url=None, voiceover_path=None):
    """
    Crea ZIP robusto con gestione errori e User-Agent.
    """
    zip_buffer = BytesIO()

    # Variabili di stato
    final_music_path = None
    final_voice_path = None

    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        
        # --- 1. VIDEO ASSETS ---
        for i, scene in enumerate(scenes):
            # FIX CRUCIALE: Cerca sia 'video_link' (app.py) che 'download' (asset_manager)
            download_link = scene.get('video_link') or scene.get('download')
            
            if download_link:
                try:
                    # SCARICAMENTO CON HEADERS (Anti-Blocco)
                    response = requests.get(download_link, headers=get_request_headers(), timeout=30, stream=True)
                    
                    if response.status_code == 200:
                        safe_key = "".join(c for c in scene['keyword'] if c.isalnum() or c in (' ','_')).replace(' ','_')
                        filename = f"Assets/{i+1:02d}_{safe_key}.mp4"
                        zip_file.writestr(filename, response.content)
                        print(f"✅ Video {i+1} scaricato.")
                    else:
                        print(f"❌ Errore Video {i+1}: Status {response.status_code}")
                        zip_file.writestr(f"Assets/ERROR_VIDEO_{i+1}_STATUS_{response.status_code}.txt", download_link)
                except Exception as e:
                    print(f"❌ Eccezione Video {i+1}: {e}")
                    zip_file.writestr(f"Assets/ERROR_VIDEO_{i+1}.txt", str(e))
            else:
                zip_file.writestr(f"Assets/MISSING_LINK_{i+1}.txt", "Nessun link trovato nel JSON")

        # --- 2. MUSIC ASSET ---
        if music_url:
            try:
                # Gestione tupla/stringa
                real_url = music_url[1] if isinstance(music_url, tuple) else music_url
                
                if real_url:
                    m_resp = requests.get(real_url, headers=get_request_headers(), timeout=30)
                    if m_resp.status_code == 200:
                        zip_file.writestr("Assets/Background_Music.mp3", m_resp.content)
                        final_music_path = "Assets/Background_Music.mp3"
                        print("✅ Musica scaricata.")
                    else:
                        print(f"❌ Errore Musica: {m_resp.status_code}")
            except Exception as e:
                print(f"❌ Eccezione Musica: {e}")

        # --- 3. VOICEOVER ASSET ---
        if voiceover_path and os.path.exists(voiceover_path):
            with open(voiceover_path, "rb") as f:
                content = f.read()
                zip_file.writestr("Assets/Voiceover.mp3", content)
                final_voice_path = "Assets/Voiceover.mp3"
                print("✅ Voiceover archiviato.")

        # --- 4. XML ---
        xml_content = generate_davinci_xml(
            "TubeFlow_Project", 
            scenes, 
            orientation, 
            music_path=final_music_path, 
            voice_path=final_voice_path
        )
        zip_file.writestr(f"Project_{orientation}.fcpxml", xml_content)

        # 5. Script
        script_text = "\n".join([f"SCENE {s['scene_number']} ({s['keyword']}): {s['voiceover']}" for s in scenes])
        zip_file.writestr("Script.txt", script_text)

    return zip_buffer.getvalue()