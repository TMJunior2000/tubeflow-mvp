import zipfile
from io import BytesIO
import requests
import os

# --- DOWNLOADER INTELLIGENTE ---
def download_asset_to_memory(url, custom_referer=None):
    referer = custom_referer if custom_referer else "https://pixabay.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": referer, 
        "Accept": "*/*"
    }
    
    try:
        print(f"⬇️ Downloading: {url} (Ref: {referer})")
        r = requests.get(url, headers=headers, allow_redirects=True, timeout=30)
        
        if r.status_code == 200 and len(r.content) > 5000: # Minimo 5KB
            return r.content
        else:
            print(f"❌ Error {r.status_code} or file too small")
            return None
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

# --- GENERATORE XML ---
def generate_davinci_xml(project_name, scenes, orientation, has_music, has_voice, fps=30):
    total_duration = sum(s['duration'] for s in scenes)
    width, height = (1080, 1920) if orientation == "portrait" else (1920, 1080)

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.8">
    <resources>
        <format id="r1" name="FFVideoFormat{height}p{fps}" frameDuration="1/{fps}s" width="{width}" height="{height}" colorSpace="1-1-1 (Rec. 709)"/>
"""
    r_id = 2
    music_rid = f"r{r_id}" if has_music else None
    if has_music: 
        xml += f'        <asset id="{music_rid}" name="Music" src="./Assets/Background_Music.mp3" start="0s" duration="{total_duration}s" hasVideo="0" hasAudio="1" audioSources="1" audioChannels="2" />\n'; r_id+=1
    
    voice_rid = f"r{r_id}" if has_voice else None
    if has_voice: 
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

# --- ZIP CREATOR ---
def create_smart_package(scenes, orientation, music_data_tuple=None, voiceover_path=None):
    zip_buffer = BytesIO()
    downloaded_music = False
    downloaded_voice = False

    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
        # 1. VIDEO
        for i, scene in enumerate(scenes):
            url = scene.get('video_link') or scene.get('download')
            if url:
                vid_content = download_asset_to_memory(url, "https://pixabay.com/")
                if vid_content: zf.writestr(f"Assets/{i+1:02d}_Clip.mp4", vid_content)

        # 2. MUSIC (Con Fallback)
        if music_data_tuple:
            page_url, mp3_url = music_data_tuple
            print(f"🎵 Download MP3. Ref: {page_url}")
            
            # Tentativo 1: Pixabay Legit
            music_content = download_asset_to_memory(mp3_url, page_url)
            
            if music_content:
                zf.writestr("Assets/Background_Music.mp3", music_content)
                downloaded_music = True
            else:
                # Tentativo 2: Fallback Indistruttibile
                print("⚠️ Pixabay failed. Using Wikimedia Fallback.")
                fb_url = "https://upload.wikimedia.org/wikipedia/commons/e/e7/Impact_Moderato_-_Kevin_MacLeod.mp3"
                fb_content = download_asset_to_memory(fb_url, "https://wikipedia.org")
                if fb_content:
                    zf.writestr("Assets/Background_Music.mp3", fb_content)
                    zf.writestr("Assets/INFO_FALLBACK.txt", "Pixabay blocked download. Used Wikimedia fallback.")
                    downloaded_music = True

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