import zipfile
from io import BytesIO
import requests
import os

def generate_davinci_xml(project_name, scenes, orientation, fps=30):
    """
    Genera FCPXML adattando la risoluzione al formato scelto.
    orientation: 'portrait' o 'landscape'
    """
    total_duration = sum(s['duration'] for s in scenes)
    
    # Setup Risoluzione
    if orientation == "portrait":
        width, height = 1080, 1920
    else:
        width, height = 1920, 1080

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.8">
    <resources>
        <format id="r1" name="FFVideoFormat{height}p{fps}" frameDuration="1/{fps}s" width="{width}" height="{height}" colorSpace="1-1-1 (Rec. 709)"/>
    </resources>
    <library>
        <event name="{project_name}">
            <project name="{project_name}">
                <sequence format="r1" duration="{total_duration}s" tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="48k">
                    <spine>
"""
    offset = 0
    for i, scene in enumerate(scenes):
        safe_keyword = "".join(c for c in scene['keyword'] if c.isalnum() or c in (' ', '_')).replace(' ', '_')
        filename = f"{i+1:02d}_{safe_keyword}.mp4"
        dur = scene['duration']
        
        xml += f"""
                        <clip name="{filename}" offset="{offset}s" duration="{dur}s" start="0s">
                            <note>{scene['voiceover']}</note>
                            <video offset="0s" ref="r1" duration="{dur}s" start="0s"/>
                        </clip>"""
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
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        
        # 1. Video
        for i, scene in enumerate(scenes):
            if scene.get('video_link'):
                try:
                    vid_content = requests.get(scene['video_link'], timeout=10).content
                    safe_key = "".join(c for c in scene['keyword'] if c.isalnum() or c in (' ','_')).replace(' ','_')
                    zip_file.writestr(f"Assets/{i+1:02d}_{safe_key}.mp4", vid_content)
                except:
                    zip_file.writestr(f"Assets/ERROR_SCENE_{i+1}.txt", "Download failed")

        # 2. Musica
        if music_url:
            try:
                music_content = requests.get(music_url, timeout=10).content
                zip_file.writestr("Assets/Background_Music.mp3", music_content)
            except: pass

        # 3. Voce
        if voiceover_path and os.path.exists(voiceover_path):
            with open(voiceover_path, "rb") as f:
                zip_file.writestr("Assets/Voiceover.mp3", f.read())

        # 4. XML & Script (Passiamo orientation all'XML generator)
        xml_content = generate_davinci_xml("TubeFlow_Timeline", scenes, orientation)
        zip_file.writestr(f"Project_{orientation}.fcpxml", xml_content)

        script_text = "\n".join([f"SCENE {s['scene_number']}: {s['voiceover']}" for s in scenes])
        zip_file.writestr("Script.txt", script_text)
        zip_file.writestr("README.txt", f"Format: {orientation.upper()}\nImport 'Assets' folder into CapCut/DaVinci.")

    return zip_buffer.getvalue()