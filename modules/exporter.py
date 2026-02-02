import zipfile
from io import BytesIO
import requests
import os

def generate_davinci_xml(project_name, scenes, fps=30):
    # ... (Codice XML identico a prima, ometto per brevità) ...
    # L'unica differenza è che se non c'è audio, l'XML dovrebbe rifletterlo, 
    # ma DaVinci ignora i file mancanti, quindi va bene lasciare così.
    return "..." # (Incolla qui la funzione generate_davinci_xml precedente)

def create_smart_package(scenes, music_url=None, voiceover_path=None):
    """
    Crea ZIP gestendo asset opzionali.
    """
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        
        # 1. Video (Sempre presenti)
        for i, scene in enumerate(scenes):
            if scene.get('video_link'):
                try:
                    vid_content = requests.get(scene['video_link'], timeout=10).content
                    safe_key = "".join(c for c in scene['keyword'] if c.isalnum() or c in (' ','_')).replace(' ','_')
                    zip_file.writestr(f"Assets/{i+1:02d}_{safe_key}.mp4", vid_content)
                except:
                    zip_file.writestr(f"Assets/ERROR_SCENE_{i+1}.txt", "Download failed")

        # 2. Musica (Opzionale)
        if music_url:
            try:
                music_content = requests.get(music_url, timeout=10).content
                zip_file.writestr("Assets/Background_Music.mp3", music_content)
            except: pass

        # 3. Voce (Opzionale)
        if voiceover_path and os.path.exists(voiceover_path):
            with open(voiceover_path, "rb") as f:
                zip_file.writestr("Assets/Voiceover.mp3", f.read())

        # 4. Script & Readme
        script_text = "\n".join([f"SCENE {s['scene_number']}: {s['voiceover']}" for s in scenes])
        zip_file.writestr("Script.txt", script_text)
        zip_file.writestr("README.txt", "Import 'Assets' folder into CapCut/DaVinci.")

    return zip_buffer.getvalue()