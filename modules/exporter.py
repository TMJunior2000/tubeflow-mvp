import zipfile
from io import BytesIO
import requests
import os

def generate_davinci_xml(project_name, scenes, orientation, music_path=None, voice_path=None, fps=30):
    """
    Genera FCPXML 1.8 includendo Video, Musica e Voiceover.
    """
    total_duration = sum(s['duration'] for s in scenes)
    total_frames = total_duration * fps
    
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
    # Gli ID r1 è il formato. Usiamo r2, r3... per i file.
    resource_id_counter = 2
    
    # Risorse Video (Non servono asset espliciti per la spine di base in FCPXML 1.8 semplice, 
    # ma per l'audio servono per forza).
    
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
        
        # Aggiungiamo il clip video
        xml += f"""
                        <clip name="{filename}" offset="{offset}s" duration="{dur}s" start="0s">
                            <note>{scene['voiceover']}</note>
                            <video offset="0s" ref="r1" duration="{dur}s" start="0s"/>
"""
        
        # --- 3. AGGANCIO AUDIO (CONNECTED CLIPS) ---
        # Colleghiamo l'audio SOLO alla prima clip video (start=0) e lo facciamo durare tutto il video
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

        xml += "                        </clip>" # Chiusura clip video
        offset += dur

    # Footer XML
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
    Crea lo ZIP finale e chiama il generatore XML aggiornato.
    """
    zip_buffer = BytesIO()

    # Variabili per tracciare se i file esistono davvero
    final_music_path = None
    final_voice_path = None

    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        
        # 1. Video Assets
        for i, scene in enumerate(scenes):
            if scene.get('download'): # Usa 'download' da asset_manager
                try:
                    vid_content = requests.get(scene['download'], timeout=15).content
                    safe_key = "".join(c for c in scene['keyword'] if c.isalnum() or c in (' ','_')).replace(' ','_')
                    zip_file.writestr(f"Assets/{i+1:02d}_{safe_key}.mp4", vid_content)
                except:
                    zip_file.writestr(f"Assets/ERROR_SCENE_{i+1}.txt", "Download failed")

        # 2. Musica (Download e salvataggio)
        if music_url:
            try:
                # Se è una tupla (page, mp3), prendi il secondo elemento
                if isinstance(music_url, tuple):
                    real_mp3_url = music_url[1]
                else:
                    real_mp3_url = music_url

                if real_mp3_url:
                    music_content = requests.get(real_mp3_url, timeout=15).content
                    zip_file.writestr("Assets/Background_Music.mp3", music_content)
                    final_music_path = "Assets/Background_Music.mp3" # Segnale che esiste
            except Exception as e: 
                print(f"Music Download Error: {e}")

        # 3. Voiceover (Lettura da file locale e salvataggio)
        if voiceover_path and os.path.exists(voiceover_path):
            with open(voiceover_path, "rb") as f:
                zip_file.writestr("Assets/Voiceover.mp3", f.read())
            final_voice_path = "Assets/Voiceover.mp3" # Segnale che esiste

        # 4. XML Generator (Passiamo i path confermati)
        # Nota: L'XML si aspetta di trovare i file relativi a se stesso.
        # Se l'XML è nella root e i file in Assets/, i path sono corretti.
        xml_content = generate_davinci_xml(
            "TubeFlow_Project", 
            scenes, 
            orientation, 
            music_path=final_music_path, 
            voice_path=final_voice_path
        )
        
        zip_file.writestr(f"Project_{orientation}.fcpxml", xml_content)

        # 5. Script Text
        script_text = "\n".join([f"SCENE {s['scene_number']}: {s['voiceover']}" for s in scenes])
        zip_file.writestr("Script.txt", script_text)
        zip_file.writestr("README.txt", f"Format: {orientation.upper()}\nImport the .fcpxml file into DaVinci Resolve.\nEnsure the 'Assets' folder is in the same directory as the XML.")

    return zip_buffer.getvalue()