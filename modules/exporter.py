import zipfile
from io import BytesIO
import requests
import os

def generate_davinci_xml(project_name, scenes, fps=30):
    """Genera file FCPXML 1.8 compatibile con DaVinci Resolve."""
    total_duration = sum(s['duration'] for s in scenes)
    
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.8">
    <resources>
        <format id="r1" name="FFVideoFormat1080p{fps}" frameDuration="1/{fps}s" width="1080" height="1920" colorSpace="1-1-1 (Rec. 709)"/>
    </resources>
    <library>
        <event name="{project_name}">
            <project name="{project_name}">
                <sequence format="r1" duration="{total_duration}s" tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="48k">
                    <spine>
"""
    offset = 0
    for i, scene in enumerate(scenes):
        # Nome file pulito es: 01_City.mp4
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

def create_smart_package(scenes, music_url, voiceover_path):
    """
    Crea uno ZIP contenente tutti gli asset fisici + XML.
    """
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        
        # 1. Download Video (Rinominati per CapCut: 01_, 02_)
        for i, scene in enumerate(scenes):
            if scene.get('video_link'):
                try:
                    # Timeout breve per evitare blocchi
                    vid_content = requests.get(scene['video_link'], timeout=15).content
                    safe_keyword = "".join(c for c in scene['keyword'] if c.isalnum() or c in (' ', '_')).replace(' ', '_')
                    filename = f"Assets/{i+1:02d}_{safe_keyword}.mp4"
                    zip_file.writestr(filename, vid_content)
                except Exception as e:
                    zip_file.writestr(f"Assets/ERROR_SCENE_{i+1}.txt", f"Error downloading: {e}")

        # 2. Download Musica
        if music_url:
            try:
                music_content = requests.get(music_url, timeout=15).content
                zip_file.writestr("Assets/Background_Music.mp3", music_content)
            except:
                pass

        # 3. Inserimento Voiceover (Generato in locale)
        if voiceover_path and os.path.exists(voiceover_path):
            with open(voiceover_path, "rb") as f:
                zip_file.writestr("Assets/Voiceover_Narrator.mp3", f.read())

        # 4. Generazione XML
        xml_content = generate_davinci_xml("TubeFlow_Timeline", scenes)
        zip_file.writestr("TubeFlow_DaVinci.fcpxml", xml_content)

        # 5. Script TXT
        script_text = "\n\n".join([f"SCENE {s['scene_number']} ({s['duration']}s)\nVISUAL: {s['keyword']}\nAUDIO: {s['voiceover']}" for s in scenes])
        zip_file.writestr("Script_Brief.txt", script_text)
        
        # 6. Leggimi
        readme = """
        ISTRUZIONI:
        - CAPCUT: Trascina l'intera cartella 'Assets' nella timeline. I file 01, 02... sono già in ordine.
        - DAVINCI RESOLVE: File > Import > Timeline... seleziona il file .fcpxml. Se i media risultano offline, usa 'Relink' puntando alla cartella Assets.
        """
        zip_file.writestr("README.txt", readme)

    return zip_buffer.getvalue()