import zipfile
from io import BytesIO
import requests
import os

def download_asset_to_memory(url, custom_referer=None):
    referer = custom_referer if custom_referer else "https://pixabay.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": referer, 
        "Accept": "*/*"
    }
    
    try:
        print(f"⬇️ DL: {url}")
        r = requests.get(url, headers=headers, allow_redirects=True, timeout=30)
        if r.status_code == 200 and len(r.content) > 5000:
            return r.content
    except Exception as e:
        print(f"DL Err: {e}")
    return None

def generate_davinci_xml(project_name, scenes, orientation, has_music, has_voice, fps=30):
    total_duration = sum(s['duration'] for s in scenes)
    width, height = (1080, 1920) if orientation == "portrait" else (1920, 1080)
    
    # XML Header
    xml = f"""<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE fcpxml><fcpxml version="1.8"><resources><format id="r1" name="FFVideoFormat{height}p{fps}" frameDuration="1/{fps}s" width="{width}" height="{height}" colorSpace="1-1-1 (Rec. 709)"/>"""
    
    r_id = 2
    # Asset Music RIMOSSO.
    
    # Asset Voice
    voice_rid = f"r{r_id}" if has_voice else None
    if has_voice: 
        xml += f'        <asset id="{voice_rid}" name="Voice" src="./Assets/Voiceover.mp3" start="0s" duration="{total_duration}s" hasVideo="0" hasAudio="1" audioSources="1" audioChannels="1" />\n'
        r_id+=1

    xml += f"""    </resources><library><event name="{project_name}"><project name="{project_name}"><sequence format="r1" duration="{total_duration}s" tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="48k"><spine>"""
    
    offset = 0
    for i, scene in enumerate(scenes):
        clean_name = f"{i+1:02d}_Clip.mp4"
        dur = scene['duration']
        xml += f"""<clip name="{clean_name}" offset="{offset}s" duration="{dur}s" start="0s"><note>{scene['voiceover']}</note><video offset="0s" ref="r1" duration="{dur}s" start="0s"/>"""
        
        # Aggiungo SOLO la traccia vocale alla prima clip
        if i == 0:
            if voice_rid: 
                xml += f'<clip lane="-1" offset="0s" ref="{voice_rid}" duration="{total_duration}s" start="0s"><audio role="dialogue"/></clip>'
            # Nessuna clip musicale qui
            
        xml += "</clip>\n"; offset += dur
    
    xml += """</spine></sequence></project></event></library></fcpxml>"""
    return xml

def create_smart_package(scenes, orientation, music_data_tuple=None, voiceover_path=None):
    zip_buffer = BytesIO()
    # has_music è forzato a False perché userai l'audio di TikTok
    downloaded_music = False 
    downloaded_voice = False

    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
        # 1. VIDEO
        for i, scene in enumerate(scenes):
            url = scene.get('video_link') or scene.get('download')
            if url:
                vid = download_asset_to_memory(url)
                if vid: zf.writestr(f"Assets/{i+1:02d}_Clip.mp4", vid)

        # 2. MUSIC - SALTATO COMPLETAMENTE
        # (Nessun download, nessun fallback, nessun file mp3)

        # 3. VOICE
        if voiceover_path and os.path.exists(voiceover_path):
            with open(voiceover_path, "rb") as f: zf.writestr("Assets/Voiceover.mp3", f.read())
            downloaded_voice = True

        # 4. XML & SCRIPT
        xml = generate_davinci_xml("TubeFlow", scenes, orientation, downloaded_music, downloaded_voice)
        zf.writestr(f"Project_{orientation}.fcpxml", xml)
        
        script = "\n".join([f"SCENE {s['scene_number']}: {s['voiceover']}" for s in scenes])
        zf.writestr("Script.txt", script)

    return zip_buffer.getvalue()